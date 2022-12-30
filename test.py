from pyjsondb import JsonDatabase

db_path = "users.db"

with JsonDatabase("users", db_path) as db:
    # add some users to the database

    for user in [
        {"name": "bob", "age": 12},
        {"name": "bobby",'children':{'name':'small',"children":{'hahaha':'123'}}},
        {"name": {"haha":"123"}},
        {"name": ["joe", "jony"]},
        {"name": "john"},
        {"name": "jones", "age": 12},
        {"name": "joey", "birthday": "may 12"}]:
        db.add_entry(user)
    # pretty print database contents
    db.print()
    #entry_id = db.get_entry_id({"name": {"haha":"123"}})
    entry_id = db.get_entry_id({"age": 12},strictly=False)
    print(entry_id)
    if isinstance(entry_id,list):
        print("pppp")
        print(entry_id[1])
        print(db.get_entry_by_id(entry_id[1]))
        db.update_entry(entry_id[1],{"name":"ttttt"})
        db.add_child_to_entry(entry_id[1],{"add_child":"is child"})
        print(db.get_child_by_entry_id(entry_id[1]))
        db.update_child_of_entry(entry_id[1],{"add_child":"another child"})
        db.delete_child_of_entry(entry_id[1])
    else:
        print(db.get_entry_by_id(entry_id))
    #print(db.get_tables())
    #db.add_table("test")
    #print(db.get_tables())
    #db.use_table("test")
    #db.print()
    #db.use_table("users")
    #db.print()
    #db.delete_table("test")
    #db.print()
    print(db.search_by_key("hahaha"))
    #r = db.get_path_by_key("hahaha",fuzzy=True)
    r = db.get_path_by_key_value("hahaha","55555",fuzzy=True)
    print("found")
    print(r)
    print("is")
    print(db.get_value_by_path(r[0]))
    db.update_value_by_path(r[0],'555555')
    db.add_child_to_path(r[0],[1,2,3,4])
    print(db.get_child_by_path(r[0]))
    print(db.update_child_of_path(r[0],[4444,77777]))
    db.delete_child_of_path(r[0])