from .db import cur
from typing import Dict
from uuid import uuid4
from .flask_app import app
from .helpers import *
from flask import request, Response


def chat_perms_wrapper(user_id: str, server_id: str, chat_id: str, cursor=cur) -> Dict:
    """
    Given a user_token, server_id, and chat_id, this function will return a dict containing bools for all the different permissions in the db based on their role
    """
    try:
        chat_query="""select read_perm_level, write_perm_level from "Discord"."ChatInfo" where chat_id = %s"""
        cursor.execute(chat_query, (chat_id,))
        perms= cursor.fetchall()[0]
        minimum_reading_level, minimum_writing_level=perms[0], perms[1]

        # Getting the user's roles from MemberInfo with the user_id and the server_id
        
        member_query="""select roles_list from "Discord"."MemberInfo" where user_id = %s and server_id= %s"""
        cursor.execute(member_query, (user_id, server_id))
        results = cursor.fetchall()
        if len(results) == 0:
            data = {"readable": False, "writeable": False}
            return Response(json.dumps({"type": "success", "data": data}), status=200)

        
        roles_list= results[0][0]

        # Getting the highest perm level for all the user's roles

        highest_perm_level=0
        for role_id in roles_list:
            perm_query="""select permissions from "Discord"."RolesInfo" where role_id = %s"""
            cursor.execute(perm_query, (role_id,))
            perm_level=int(cursor.fetchall()[0][0])

            if perm_level>highest_perm_level:
                highest_perm_level=perm_level
        
        # Checking to see if user's highest perm level >= the needed perm level to read/write

        readable=False
        writeable=False
        if highest_perm_level>=minimum_reading_level:
            readable=True
        if highest_perm_level>=minimum_writing_level:
            writeable=True

        data = {"readable":readable, "writeable":writeable}
        return data
    except Exception as e:
        return {"readable": False, "writeable": False}

# API
@app.route("/api/roles/get_chat_perms", methods=["POST"])
def get_chat_perms() -> Dict:
    
    # Stuff for testing- ignore

    # user_id='b98757df-71aa-4615-8345-26c71cfbb304'
    # server_id='ad3f1cd8-ffcd-48ca-abc7-9409c17c9122'
    # chat_id='43eef70b-90bb-40c5-8ece-45abf6a55abb'

    if not validate_fields(request.json, {"user_token": str, "server_id": str, "chat_id": str}):
        return invalid_fields()
    
    user_token = request.json["user_token"]
    if not is_valid_token(user_token):
        return forbidden()
    user_id = get_user_id(user_token)
    server_id = request.json["server_id"]
    chat_id = request.json["chat_id"]
    
    # Using the chat_id to pull the perm info from ChatInfo
    try:
        data = chat_perms_wrapper(user_token, server_id, chat_id)
        return Response(json.dumps({"type": "success", "data": data}), status=200)
    except Exception as e:
        return return_error(e)

# Given a user_id and a server_id, this function will return a dict containing bools for all the different permissions in the db based on their role
# API
@app.route("/api/roles/get_server_perms", methods=["POST"])
def get_server_perms() -> Dict:

    # Stuff for testing- ignore

    # user_id='d7c67d16-09b6-4910-9d95-96d3d430a1b9'
    # server_id='ad3f1cd8-ffcd-48ca-abc7-9409c17c9122'

    # Getting the user's roles from MemberInfo with the user_id and the server_id

    if not validate_fields(request.json, {"user_id": str, "server_id": str}):
        return invalid_fields()
    
    user_id = request.json["user_id"]
    server_id = request.json["server_id"]

    try:
        member_query="""select roles_list from "Discord"."MemberInfo" where user_id = %s and server_id= %s"""
        cur.execute(member_query, (user_id, server_id))
        roles_list = cur.fetchall()
        roles_list = roles_list[0][0]

        perms={"manage_server":False, "manage_chats":False, "manage_members":False, "manage_roles":False, "manage_voice":False,  
            "manage_messages":False, "is_admin":False}
        list_perms=list(perms.items())

        # Getting all the perms based on the list of roles and updating the dict (which combines all the perms of all the roles the user has)

        for role_id in roles_list:
            perm_query="""select manage_server, manage_chats, manage_members, manage_roles, manage_voice, manage_messages, is_admin from "Discord"."RolesInfo" where role_id = %s"""
            cur.execute(perm_query, (role_id,))
            perm_arr=cur.fetchall()[0]
            
            # Checking to see if a role has a permission that isn't already true in the dict

            for i in range(0,len(perm_arr)):
                if not perms[list_perms[i][0]] and perm_arr[i]:
                    perms[list_perms[i][0]]=True
        
        # If the user is an admin, all perms should be true

        if perms["is_admin"]:
            for key in perms:
                perms[key]=True
        
        return Response(json.dumps({"type": "success", "data": perms}), status=200)
    except Exception as e:
        return return_error(e)
        

# API
@app.route("/api/roles/create_role", methods=["POST"])
def handle_role_creation():
    if not validate_fields(request.json, {"server_id": str, 
                                          "role_name": str, 
                                          "role_color": str, 
                                          "role_symbol": str, 
                                          "priority": int, 
                                          "permissions": int, 
                                          "manage_server": bool, 
                                          "manage_chats": bool, 
                                          "manage_members": bool, 
                                          "manage_roles": bool, 
                                          "manage_voice": bool, 
                                          "manage_messages": bool, 
                                          "is_admin": bool}):
        return invalid_fields()
    
    data = request.json
    if data["is_admin"]:
        for key in ["manage_server", "manage_chats", "manage_members", "manage_roles", "manage_voice", "manage_messages"]:
            data[key] = True

    copy = data["server_id"]
    data = {k: v for k, v in data.items() if k != "server_id"}

    # data_dict = {
    #     "role_name": role_name,
    #     "role_color": role_color,
    #     "role_symbol": role_symbol,
    #     "priority": priority,
    #     "permissions": permissions,
    #     "manage_server": manage_server,
    #     "manage_chats": manage_chats,
    #     "manage_members": manage_members,
    #     "manage_roles": manage_roles,
    #     "manage_voice": manage_voice,
    #     "manage_messages": manage_messages,
    #     "is_admin":is_admin
    # }

    # # If is_admin is True, the user should have all the perms

    # if is_admin:
    #     for key in data_dict:
    #         data_dict[key]=True
    try:
        id_ = add_role(copy, data)
        ret = {
            "type": "success",
            "role_id": id_
        }
        return Response(json.dumps(ret), status=200)
    except Exception as e:
        return return_error(e)

# Given a user_id, server_id, and dict containing information about a new role, this function will add the new role to the database

def add_role(server_id:str, role_info:Dict, user_id=None) -> None:
    
    role_id=str(uuid4())

    if "id_override" in role_info:
        role_id = server_id + "_" + role_info["id_override"]

    send_query='''insert into "Discord"."RolesInfo" (role_id, server_id, role_name, role_color, role_symbol, priority, permissions, manage_server, manage_chats, \
       manage_members, manage_roles, manage_voice, manage_messages, is_admin) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
    cur.execute(send_query, (role_id, server_id, role_info['role_name'], role_info['role_color'], role_info['role_symbol'], role_info['priority'], role_info['permissions'], \
        role_info['manage_server'], role_info['manage_chats'], role_info['manage_members'], role_info['manage_roles'], role_info['manage_voice'], \
        role_info['manage_messages'], role_info['is_admin']))
    
    # If user_id is not None, the new role will be assigned to that user

    if user_id is not None:

        # Getting the user's roles from MemberInfo with the user_id and the server_id

        member_query="""select roles_list from "Discord"."MemberInfo" where user_id = %s and server_id= %s"""
        cur.execute(member_query, (user_id, server_id))
        roles_list= cur.fetchall()[0][0]
        
        # Adding the new role to roles_list
        
        roles_list.append(role_id)

        # Updating the table with the new roles_list value

        query='''update "Discord"."MemberInfo" set roles_list = %s where user_id = %s and server_id = %s'''
        cur.execute(query, (roles_list, user_id, server_id))

    return role_id


# Given a role_id, remove all instances of that role from the server
@app.route("/api/roles/remove_role", methods=["POST"])
def remove_role() -> None:

    if not validate_fields(request.json, {"role_id": str, "server_id": str}):
        return invalid_fields()
    
    role_id = request.json["role_id"]
    server_id = request.json["server_id"]

    # Remove the role from RolesInfo

    try:
        query='''delete from "Discord"."RolesInfo" where role_id = %s '''
        cur.execute(query, (role_id,))

        # Get a list of all the rows from MemberInfo containing the server_id

        query='''select * from "Discord"."MemberInfo" where server_id=%s'''
        cur.execute(query, (server_id,))
        rows=cur.fetchall()

        # Going through each row, removing the role from each user's role_list if it exists, and updating the roles_list in the table

        for row in rows:
            roles=row[7]
            user_id=row[1]
            if role_id in roles:
                roles.remove(role_id)
            query='''update "Discord"."MemberInfo" set roles_list = %s where user_id = %s and server_id = %s'''
            cur.execute(query, (roles, user_id, server_id))
        return return_success()
    except Exception as e:
        return return_error(e)

# Given a role_id get a list of all the perms for that role
# API

@app.route("/api/roles/get_perms_from_role", methods=["POST"])
def get_perms_from_role() -> Dict:

    # Pulling tuple by querying database

    if not validate_fields(request.json, {"role_id": str}):
        return invalid_fields()
    
    role_id = request.json["role_id"]


    query="""select manage_server, manage_chats, manage_members, manage_roles, manage_voice, manage_messages, is_admin from \
        "Discord"."RolesInfo" where role_id = %s"""
    
    try:
        cur.execute(query, (role_id,))
        rows=cur.fetchall()[0]

        # Formatting perms into dict

        perm_dict = {
            "manage_server": rows[0],
            "manage_chats": rows[1],
            "manage_members": rows[2],
            "manage_roles": rows[2],
            "manage_voice": rows[3],
            "manage_messages": rows[4],
            "is_admin":rows[5]
        }

        # If is_admin is True, then the user should have all the perms

        if rows[5]:
            for key in perm_dict:
                perm_dict[key]=True

        return Response(json.dumps({"type": "success", "data": perm_dict}), status=200)
    except Exception as e:
        return return_error(e)
