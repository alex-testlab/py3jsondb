# PyJsonDB

Python dict based database with persistence and search capabilities

For those times when you need something simple and sql is overkill

support add, update, delete in any level nested json tree

## Features

- pure python
- save and load from file
- search recursively by key and key/value pairs
- fuzzy search
- supports arbitrary objects
- supports comments in saved files
- supports operation in any level nested json tree

## Install

```bash
pip3 install pyjsondb
```

## Usage

### Json Format

```python
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
```

### JsonDatabase

Ever wanted to search a dict?

Let's create a dummy database with users
and Add some entrys of users

```python
from pyjsondb import JsonDatabase

db_path = "users.db"

with JsonDatabase("users", db_path) as db:
    # add some users to the database

    for user in [
        {"name": "bob", "age": 12},
        {"name": "bobby"},
        {"name": ["joe", "jony"]},
        {"name": "john"},
        {"name": "jones", "age": 35},
        {"name": "joey", "birthday": "may 12"}]:
        db.add_entry(user)
        
    # pretty print database contents
    db.print()


# auto saved when used with context manager
# db.save()


```

add, change,delete table

```python
from pyjsondb import JsonDatabase

db_path = "users.db"

with JsonDatabase("users", db_path) as db:
    
    db.add_table("test")
    # add a new table, now you have two tables: users and test
    # and change the current table to test.
    db.use_table("users")
    # change the current table to users.
    db.delete_table("test")
    #delete the table test, now have only one table:users.

```

updating an existing entry and remove entry

```python
# get database item
item = {"name": "bobby"}

item_id = db.get_entry_id(item)

if item_id >= 0:
    new_item = {"name": "don't call me bobby"}
    db.update_entry(item_id, new_item)
else:
    print("item not found in database")

db.remove_entry(item_id)
# clear changes since last commit
db.reload()
```

add, update and delete child in entrys

```python
from pyjsondb import JsonDatabase

db_path = "users.db"

with JsonDatabase("users", db_path) as db:
    
    db.add_entry({"name":"john","age":"33"})
    # add a new entry
    entry_id = db.get_entry_id({"name":"john"},strictly=False)
    # get the entry id
    db.add_child_to_entry(entry_id,{"name":"bobby","age":12})
    # add child to entry
    db.update_child_of_entry(entry_id,{"name":"bobby","age":15})
    # update child of entry to new value
    db.delete_child_of_entry(entry_id)
    # delete child of entry

```

add, update and delete any node  in any nested json tree

```python
from pyjsondb import JsonDatabase

db_path = "users.db"

with JsonDatabase("users", db_path) as db:
    
    entry_id = db.add_entry({"name":"john","age":"33"})
    # add a new entry
    db.add_child_to_entry(entry_id,{"name":"bobby","age":12})
    # add child to entry
    child_path = db.get_child_path_of_entry(entry_id)
    # get the path of entry
    #child_path = db.get_path_by_key_value("name","bobby")[0]
    # get the path via name and bobby
    db.add_child_to_path(child_path,{"grade":100})
    # add child to the path
    db.delete_child_of_path(child_path)
    # delete child of path

```


search entries by key

```python
from pyjsondb import JsonDatabase

db_path = "users.db"

db = JsonDatabase("users", db_path) # load db created in previous example

# search by exact key match, return a list of result
users_with_defined_age = db.search_by_key("age")

for user in users_with_defined_age:
    print(user["name"], user["age"])
    
# fuzzy search
users = db.search_by_key("birth", fuzzy=True)
for user, conf in users:
    print("matched with confidence", conf)
    print(user["name"], user["birthday"])
```

search by key value pair

```python
# search by key/value pair
users_12years_old = db.search_by_value("age", 12)

for user in users_12years_old:
    assert user["age"] == 12

# fuzzy search
jon_users = db.search_by_value("name", "jon", fuzzy=True)
for user, conf in jon_users:
    print(user["name"])
    print("matched with confidence", conf)
    # NOTE that one of the users has a list instead of a string in the name, it also matches
```

You can save arbitrary objects to the database

```python
from pyjsondb import JsonDatabase

db = JsonDatabase("users", "~/databases/users.json")


class User:
    def __init__(self, email, key=None, data=None):
        self.email = email
        self.secret_key = key
        self.data = data

user1 = User("first@mail.net", data={"name": "jonas", "birthday": "12 May"})
user2 = User("second@mail.net", "secret", data={"name": ["joe", "jony"], "age": 12})

# objects will be "jsonified" here, they will no longer be User objects
# if you need them to be a specific class use some ORM lib instead (SQLAlchemy is great)
db.add_entry(user1)
db.add_entry(user2)

# search entries with non empty key
print(db.search_by_key("secret_key"))

# search in user provided data
print(db.search_by_key("birth", fuzzy=True))

# search entries with a certain value
print(db.search_by_value("age", 12))
print(db.search_by_value("name", "jon", fuzzy=True))

```