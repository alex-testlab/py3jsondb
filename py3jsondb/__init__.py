from py3jsondb.utils import *
from py3jsondb.jsonpath import JsonPath
from py3jsondb.exceptions import InvalidEntryID, DatabaseNotCommitted, \
    SessionError, MatchError, TableNotFound,TableCanNotBeEmpty,ChildNotFound
from os.path import expanduser, isdir, dirname, exists, isfile, join
from os import makedirs, remove
import json
import logging
from pprint import pprint
from xdg import BaseDirectory
from py3jsondb.utils.combo_lock import ComboLock, DummyLock

from tempfile import gettempdir

LOG = logging.getLogger("JsonDatabase")


class JsonStorage(dict):
    """
    persistent python dict
    """

    def __init__(self, path, disable_lock=False):
        super().__init__()
        lock_path = join(gettempdir(), path.split("/")[-1] + ".lock")
        if disable_lock:
            LOG.warning("Lock is disabled, database might get corrupted if "
                        "different processes try to use it at same time!")
            self.lock = DummyLock(lock_path)
        else:
            self.lock = ComboLock(lock_path)
        self.path = path
        if self.path:
            self.load_local(self.path)

    def load_local(self, path):
        """
            Load local json file into self.

            Args:
                path (str): file to load
        """
        with self.lock:
            path = expanduser(path)
            if exists(path) and isfile(path):
                self.clear()
                try:
                    config = load_commented_json(path)
                    for key in config:
                        self[key] = config[key]
                    LOG.debug("Json {} loaded".format(path))
                except Exception as e:
                    LOG.error("Error loading json '{}'".format(path))
                    LOG.error(repr(e))
            else:
                LOG.debug("Json '{}' not defined, skipping".format(path))

    def clear(self):
        for k in dict(self):
            self.pop(k)

    def reload(self):
        if exists(self.path) and isfile(self.path):
            self.load_local(self.path)
        else:
            raise DatabaseNotCommitted

    def store(self, path=None):
        """
            store the json db locally.
        """
        with self.lock:
            path = path or self.path
            if not path:
                LOG.warning("json db path not set")
                return
            path = expanduser(path)
            if dirname(path) and not isdir(dirname(path)):
                makedirs(dirname(path))
            with open(path, 'w', encoding="utf-8") as f:
                json.dump(self, f, indent=4, ensure_ascii=False)

    def remove(self):
        with self.lock:
            if isfile(self.path):
                remove(self.path)

    def merge(self, conf, merge_lists=True, skip_empty=True, no_dupes=True,
              new_only=False):
        merge_dict(self, conf, merge_lists, skip_empty, no_dupes, new_only)
        return self

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.store()
        except Exception as e:
            LOG.error(e)
            raise SessionError


class JsonDatabase(object):
    """ 
    searchable persistent dict. support add, update, delete in any level nested json tree.

    format in database:
        {
            'table1 name':[
                            {'entry1_item1_name':'entry1_item1_value,'entry1_item2_name':'entry1_item2_value,....},
                            {'entry2_item1_name':'entry2_item1_value','entry2_item2_name':'entry2_item2_value',....},
                            .........
                            ]
            'table2 name':[
                            ........
                            ]
        }

    :param table_name: table name of database   
    :type table_name: str
    :param path: json file path     
    :type path: str
    :param disable_lock: disable lock
    :type disable_lock: boolean
    :param extension: extension
    :type extension: str
    """
    def __init__(self,
            table_name,
            path=None,
            disable_lock=False,
            extension="json"):
        self.tables = []
        self.name = table_name
        self.tables.append(self.name)
        self.path = path or f"{self.name}.{extension}"
        self.db = JsonStorage(self.path, disable_lock=disable_lock)

        self.db[self.name] = []
        self.db.load_local(self.path)
        try:
            self.get_tables()
        except Exception as e:
            pass



    # operator overloads
    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.save()
        except Exception as e:
            LOG.error(e)
            raise SessionError

    def __repr__(self):
        return str(jsonify_recursively(self.db[self.name]))

    def __len__(self):
        return len(self.db.get(self.name, []))

    def __getitem__(self, entry):
        if not isinstance(entry, int):
            try:
                entry_id = int(entry)
            except Exception as e:
                entry_id = self.get_entry_id(entry)
                if entry_id < 0:
                    raise InvalidEntryID
        else:
            entry_id = entry
        if entry_id >= len(self.db[self.name]):
            raise InvalidEntryID
        return self.db[self.name][entry_id]

    def __setitem__(self, entry_id, value):
        if not isinstance(entry_id, int) or entry_id >= len(self.db[self.name]) or entry_id < 0:
            raise InvalidEntryID
        else:
            self.update_entry(entry_id, value)

    def __iter__(self):
        for entry in self.db[self.name]:
            yield entry

    def __contains__(self, entry):
        entry = jsonify_recursively(entry)
        return entry in self.db[self.name]

    # database
    def save(self):
        """
            store the json db locally.
        """
        self.db.store(self.path)

    def reload(self):
        """
            reload json db
        """
        self.db.reload()

    def delete_database(self):
        """
            delete the current json db
        """
        self.db.remove()

    def print(self):
        """
            print the json tree of current table
        """
        pprint(jsonify_recursively(self.db[self.name]))

    def add_table(self,table_name):
        """
            add table in database

        :param table_name: table name
        :type table_name: str
        """
        if table_name not in self.tables:
            self.db[table_name] = []
            self.save()
        self.name = table_name
        self.get_tables()
    
    def use_table(self,table_name):
        """
            change current table in database

        :param table_name: table name
        :type table_name: str
        """
        if table_name not in self.tables:
            raise TableNotFound
        self.name = table_name

    def get_tables(self):
        """
            get all tables of database

        :return: all tables of database
        :rtype: list
        """
        self.reload()
        self.tables = list(self.db.keys())
        return self.tables

    def delete_table(self,table_name):
        """
            delete table in database

        :param table_name: table name
        :type table_name: str
        """
        if table_name not in self.tables:
            raise TableNotFound
        if len(self.tables)==1:
            raise TableCanNotBeEmpty
        if self.name == table_name:
            self.name = self.tables[0]
        self.db.pop(table_name)
        self.save()
        self.get_tables()

    # item manipulations
    def _append_entry(self, entry):
        entry = jsonify_recursively(entry)
        self.db[self.name].append(entry)
        return len(self.db[self.name])

    def add_entry(self, entry, allow_duplicates=False):
        """ 
        add an entry to current table

        :param entry: the entry you want to added
        :type entry: dict or list
        :param allow_duplicates: if allow_duplicates is True, entry is added unconditionally,else only if no exact match is present
        :type allow_duplicates: boolean
        :return: the entry id
        :rtype: int
        """
        if allow_duplicates or entry not in self:
            self._append_entry(entry)
            return len(self.db[self.name])
        return self.get_entry_id(entry)


    def match_entry(self, entry, strictly=True):
        """ 
        match entry to some entry in database
        returns a list of matched entrys

        :param entry: the entry you want to match
        :type entry: dict or list
        :param strictly: match exactly or not
        :type strictly: boolean
        :return: the matches list
        :rtype: list
        """
        entry = jsonify_recursively(entry)
        matches = []
        for idx, data in enumerate(self.db[self.name]):
            # TODO match strategy
            # - require exact match
            # - require list of keys to match
            # - require at least one of key list to match
            # - require at exactly one of key list to match

            # by default check for exact matches
            if strictly:
                if data == entry:
                    matches.append((data, idx))
            else:
                if entry.items() < data.items():
                    matches.append((data, idx))
        return matches

    def merge_entry(self, entry, entry_id=None, match_strategy=None,
                   merge_strategy=None):
        """ search an entry according to match criteria, merge fields"""
        if entry_id is None:
            matches = self.match_entry(entry, match_strategy)
            if not matches:
                raise MatchError
            match, entry_id = matches[0][1]
        else:
            match = self.db[self.name][entry_id]
        # TODO merge strategy
        # - only merge some keys
        # - dont merge some keys
        # - merge all keys
        # - dont overwrite keys
        entry = jsonify_recursively(entry)
        self.db[self.name][entry_id] = merge_dict(match, entry)


    # item_id
    def get_entry_id(self, entry,strictly=True):
        """
        get entry_id of current table
        entry_id is simply the index of the entry in the table
        WARNING: this is not immutable across sessions

        :param entry: the entry you want to match
        :type entry: dict or list
        :param strictly: match exactly or not
        :type strictly: boolean
        :return: the entry id list, return -1 if not found
        :rtype: list
        """
        idx_list = []
        for match, idx in self.match_entry(entry,strictly):
            idx_list.append(idx)
        if len(idx_list) >1:
            return idx_list
        elif len(idx_list) ==1:
            return idx_list[0]
        else:
            return -1


    def get_entry_id_by_key_value(self,key,value,strictly=False):
        """
        used for get entry id by {key:value} entry

        :param key: one key of entry
        :type key: str
        :param value: one value of entry
        :type value: any
        :param strictly: match exactly or not
        :type strictly: boolean
        :return: the entry id list, return -1 if not found
        :rtype: list
        """
        entry = {key,value}
        return self.get_entry_id(entry,strictly)

    def get_entry_by_id(self,entry_id):
        """
        get all entry info by entry id

        :param entry_id: the entry id
        :type entry_id: int
        :return: the entry info
        :rtype: dict
        """
        return self.db[self.name][entry_id]

    def get_entry_path_by_id(self,entry_id):
        """
        get entry path by entry id

        :param entry_id: the entry id
        :type entry_id: int
        :return: the entry path
        :rtype: list
        """
        return [self.name,entry_id]

    def get_child_by_entry_id(self,entry_id,child_name='children'):
        """
        get the child node of entry by entry id

        :param entry_id: the entry id
        :type entry_id: int
        :param child_name: custom child node name
        :type child_name: str
        :return: the child info
        :rtype: dict
        """ 
        entry = self.db[self.name][entry_id]
        if child_name in list(entry.keys()):
            return self.db[self.name][entry_id][child_name]
        else:
            raise ChildNotFound

    def add_child_to_entry(self,entry_id,child_data,child_name='children'):
        """
        add the child node to entry by entry id

        :param entry_id: the entry id
        :type entry_id: int
        :param child_data: the child data to add
        :type child_data: any
        :param child_name: custom child node name
        :type child_name: str
        """ 
        entry = self.db[self.name][entry_id]
        entry[child_name] = child_data

    def get_child_path_of_entry(self,entry_id,child_name='children'):
        """
        get the child node path

        :param entry_id: the entry id
        :type entry_id: int
        :param child_name: custom child node name
        :type child_name: str
        :return: the child path
        :rtype: list
        """ 
        return [self.name,entry_id,child_name]

    def update_child_of_entry(self,entry_id,child_data,overwrite=True,child_name='children'):
        """
        update the child node of entry by entry id

        :param entry_id: the entry id
        :type entry_id: int
        :param child_data: the child data to update
        :type child_data: any
        :param overwrite: if set false, can update dict data
        :type overwrite: boolean
        :param child_name: custom child node name
        :type child_name: str
        """ 
        entry = self.db[self.name][entry_id]
        if overwrite:
            entry[child_name] = child_data
        else:
            if isinstance(child_data,dict):
                entry[child_name].update(child_data)
            else:
                raise Exception("only dict can use overwrite=False")

    def delete_child_of_entry(self,entry_id,child_name='children'):
        """
        delete the child node of entry by entry id

        :param entry_id: the entry id
        :type entry_id: int
        :param child_name: custom child node name
        :type child_name: str
        """ 
        entry = self.db[self.name][entry_id]
        if child_name in list(entry.keys()):
            self.db[self.name][entry_id].pop(child_name)
        else:
            raise ChildNotFound

    def update_entry(self, entry_id, new_entry,overwrite=True):
        """
        update the entry of table by entry id

        :param entry_id: the entry id
        :type entry_id: int
        :param new_entry: the entry data to update
        :type new_entry: any
        :param overwrite: if set false, can update dict data
        :type overwrite: boolean
        """
        new_entry = jsonify_recursively(new_entry)
        if overwrite:
            self.db[self.name][entry_id] = new_entry
        else:
            if isinstance(new_entry,dict):
                self.db[self.name][entry_id].update(new_entry)
            else:
                raise Exception("only dict can use overwrite=False")

    def remove_entry(self, entry_id):
        """
        delete the entry of table by entry id

        :param entry_id: the entry id
        :type entry_id: int
        """
        res = self.db[self.name].pop(entry_id)
        return res

    # search
    def search_by_key(self, key, fuzzy=False, thresh=0.7, include_empty=False):
        """
        search key in database

        :param key: the key that want to search
        :type key: str
        :param fuzzy: fuzzy search or not
        :type fuzzy: boolean
        :param thresh: the threshold of match
        :type thresh: double
        :return: search result
        :rtype: list
        """ 
        if fuzzy:
            return get_key_recursively_fuzzy(self.db, key, thresh, not include_empty)
        return get_key_recursively(self.db, key, not include_empty)

    def search_by_value(self, key, value, fuzzy=False, thresh=0.7):
        """
        search key and value in database

        :param key: the key that want to search
        :type key: str
        :param value: the value that want to search
        :type value: str
        :param fuzzy: fuzzy search or not
        :type fuzzy: boolean
        :param thresh: the threshold of match
        :type thresh: double
        :return: search result
        :rtype: list
        """ 
        if fuzzy:
            return get_value_recursively_fuzzy(self.db, key, value, thresh)
        return get_value_recursively(self.db, key, value)

    def get_path_by_key(self,key,fuzzy=False,thresh=0.7):
        """
        get the detail path by key

        :param key: the key that want to search
        :type key: str
        :param fuzzy: fuzzy search or not
        :type fuzzy: boolean
        :param thresh: the threshold of match
        :type thresh: double
        :return: detail path
        :rtype: list
        """ 
        jp = JsonPath(self.db,mode = 'key',fuzzy=fuzzy,thresh=thresh)
        paths = jp.find_all(key)
        return paths
    
    def get_path_by_value(self,value,fuzzy=False,thresh=0.7):
        """
        get the detail path by value

        :param value: the value that want to search
        :type value: str
        :param fuzzy: fuzzy search or not
        :type fuzzy: boolean
        :param thresh: the threshold of match
        :type thresh: double
        :return: detail path
        :rtype: list
        """ 
        jp = JsonPath(self.db,mode = 'value',fuzzy=fuzzy,thresh=thresh)
        paths = jp.find_all(value)
        return paths

    def get_path_by_key_value(self,key,value,fuzzy=False,thresh=0.7):
        """
        get the detail path by key and value

        :param key: the key that want to search
        :type key: str
        :param value: the value that want to search
        :type value: str
        :param fuzzy: fuzzy search or not
        :type fuzzy: boolean
        :param thresh: the threshold of match
        :type thresh: double
        :return: detail path
        :rtype: list
        """ 
        jp = JsonPath(self.db,mode = 'key_value',fuzzy=fuzzy,thresh=thresh)
        paths = jp.find_all({key:value})
        return paths

    def update_value_by_path(self,path,new_value):
        """
        update value by path

        :param path: the path of node
        :type path: list
        :param new_value: the updated value
        :type new_value: any
        """ 
        obj_ptr = self.db
        for key in path:
            if key == path[-1]:
                obj_ptr[key] = new_value
            obj_ptr = obj_ptr[key]

    def get_value_by_path(self,path):
        """
        get the value by path

        :param path: the path of node
        :type path: list
        :return: the value of node
        :rtype: any
        """ 
        data = self.db
        for p in path:
            data = data[p]
        if data is not None:
            return data
        return None

    def get_object_by_path(self,path):
        """
        get the object by path

        :param path: the path of node
        :type path: list
        :return: the object of node
        :rtype: object
        """ 
        obj_ptr = self.db
        for key in path:
            if key == path[-1]:
                return obj_ptr
            obj_ptr = obj_ptr[key]
        return None

    def get_child_by_path(self,path,child_name='children'):
        """
        get the child info by path

        :param path: the path of node
        :type path: list
        :param child_name: the custom child name
        :type child_name: str
        :return: the child info of node
        :rtype: any
        """ 
        val = self.get_object_by_path(path)
        if child_name in list(val.keys()):
            return val[child_name]
        else:
            raise ChildNotFound


    def add_child_to_path(self,path,child_data,child_name='children'):
        """
        add the child to path

        :param path: the path of node
        :type path: list
        :param child_data: the child info to add
        :type child_data: any
        :param child_name: the custom child name
        :type child_name: str
        """ 
        val = self.get_object_by_path(path)
        val[child_name] = child_data

    def update_child_of_path(self,path,child_data,overwrite=True,child_name='children'):
        """
        update the child of path

        :param path: the path of node
        :type path: list
        :param child_data: the child info to update
        :type child_data: any
        :param overwrite: can update the dict if set false
        :type overwrite: boolean
        :param child_name: the custom child name
        :type child_name: str
        """ 
        val = self.get_object_by_path(path)
        if overwrite:
            val[child_name] = child_data
        else:
            if isinstance(child_data,dict):
                val[child_name].update(child_data)
            else:
                raise Exception("only dict can use overwrite=False")


    def delete_child_of_path(self,path,child_name='children'):
        """
        delete the child of path

        :param path: the path of node
        :type path: list
        :param child_name: the custom child name
        :type child_name: str
        """ 
        val = self.get_object_by_path(path)
        val.pop(child_name)

# XDG aware classes

class JsonStorageXDG(JsonStorage):
    """ xdg respectful persistent dicts """

    def __init__(self,
                 name,
                 xdg_folder=BaseDirectory.xdg_cache_home,
                 disable_lock=False, subfolder="json_database",
                 extension="json"):
        self.name = name
        path = join(xdg_folder, subfolder, f"{name}.{extension}")
        super().__init__(path, disable_lock=disable_lock)


class JsonDatabaseXDG(JsonDatabase):
    """ xdg respectful json database """

    def __init__(self, name, xdg_folder=BaseDirectory.xdg_data_home,
                 disable_lock=False, subfolder="json_database",
                 extension="jsondb"):
        path = join(xdg_folder, subfolder, f"{name}.{extension}")
        super().__init__(name, path, disable_lock=disable_lock, extension=extension)

class JsonConfigXDG(JsonStorageXDG):
    """ xdg respectful config files, using json_storage.JsonStorageXDG """

    def __init__(self, name, xdg_folder=BaseDirectory.xdg_config_home,
                 disable_lock=False, subfolder="json_database",
                 extension="json"):
        super().__init__(name, xdg_folder, disable_lock, subfolder, extension)
