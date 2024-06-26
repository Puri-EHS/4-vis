import uuid
import blessed
term = blessed.Terminal()
import colors
import cursor
import keyshortcuts
import requests
import config
import registry
import sys

global selection
selection = 0
selected = None

global cursor_pos
cursor_pos = 0

global code
code = ""

global error_show
error_show = False

global user_token
user_token = None


FIELD_WIDTH = int(term.width * 0.4 - 8) - 1


def hex_to_rgb(hex):
    hex = hex.lstrip('#')
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

def draw_background():
    print(term.home + term.clear, end=" ")
    for y in range(term.height):
        print(term.move(y, 0) + term.on_color_rgb(*hex_to_rgb(colors.background)) + ' ' * term.width, end="")

def draw_menu():
    tlx = int(term.width * 0.3)
    tly = int(term.height * 0.2)

    for y in range(tly, tly + int(term.height * 0.6)):
        print(term.move(y, tlx) + term.on_color_rgb(*hex_to_rgb(colors.div)) + ' ' * int(term.width * 0.4), end="")

    print(term.move(tly-1, tlx-1) + term.on_color_rgb(*hex_to_rgb(colors.background)) + term.color_rgb(*hex_to_rgb(colors.div_shadow)) + "▄" * int(term.width * 0.4 + 2), end="")
    print(term.move(tly + int(term.height * 0.6), tlx-1) + term.on_color_rgb(*hex_to_rgb(colors.background)) + term.color_rgb(*hex_to_rgb(colors.div_shadow)) + "▀" * int(term.width * 0.4 + 2), end="")
    for y in range(tly, tly + int(term.height * 0.6)):
        print(term.move(y, tlx-1) + term.on_color_rgb(*hex_to_rgb(colors.div_shadow)) + " ", end="")
        print(term.move(y, tlx + int(term.width * 0.4)) + term.on_color_rgb(*hex_to_rgb(colors.div_shadow)) + " ", end="")



def center_text(text):
    return int(term.width / 2 - len(text) / 2)

def draw_all_text():
    x = center_text("Join Server")
    print(term.move(int(term.height*0.35) - 2, x) + term.on_color_rgb(*hex_to_rgb(colors.div)) + term.color_rgb(*hex_to_rgb(colors.header)) + "Join Server", end="")


    x = center_text("Server Code")
    print(term.move_yx(int(term.height*0.5) - 4, x) + term.color_rgb(*hex_to_rgb(colors.text)) + term.on_color_rgb(*hex_to_rgb(colors.div)) + term.bold("Server Code"), end="")
    

def draw_fields():
    global selection, cursor_pos
    if selection == 0:
        f1 = colors.field_highlighted
    else:
        f1 = colors.field

    if len(code) == 0:
        t1 = colors.unselected_text
    else:
        t1 = colors.text
    



    print(term.move_yx(int(term.height*0.5) - 3, int(term.width * 0.3) + 4) + term.on_color_rgb(*hex_to_rgb(f1)) + " " * int(term.width * 0.4 - 8), end="")
    


    chunks = [code[i:i+FIELD_WIDTH] for i in range(0, len(code), FIELD_WIDTH)]
    if len(code) == 0:
        if selection != 0:
            display_code = "..."
        else:
            display_code = ""
    else:
        display_code = chunks[-1]
    
    if len(chunks) > 1:
        print(term.move_yx(int(term.height*0.5) - 3, int(term.width * 0.3) + 4 - 1) + term.on_color_rgb(*hex_to_rgb(colors.div)) + term.cyan + "<", end="")
    else:
        print(term.move_yx(int(term.height*0.5) - 3, int(term.width * 0.3) + 4 - 1) + term.on_color_rgb(*hex_to_rgb(colors.div)) + term.cyan + " ", end="")
    
    print(term.move_yx(int(term.height*0.5) - 3, int(term.width * 0.3) + 4) + term.color_rgb(*hex_to_rgb(t1)) + term.on_color_rgb(*hex_to_rgb(f1)) + display_code, end="")



    if selection == 0:
        y = int(term.height*0.5) - 3
        cursor_pos = len(display_code)
        
        print(term.move_yx(y, int(term.width * 0.3) + 4 + min(cursor_pos, FIELD_WIDTH)) + term.on_color_rgb(*hex_to_rgb(colors.cursor)) + " ", end="")


def draw_buttons():
    global selection
    x = center_text("Join") - 3
    if selection == 2:
        color = colors.button_selected
    else:
        color = colors.button
    print(term.move(int(term.height*0.65), x) + term.on_color_rgb(*hex_to_rgb(color)) + term.color_rgb(*hex_to_rgb(colors.text)) + term.bold(" " * 3 + "Join" + " " * 3), end="")

def display_error(msg):
    if not msg:
        print(term.move(int(term.height*0.65) + 2, int(term.width * 0.3)) + term.on_color_rgb(*hex_to_rgb(colors.div)) + " " * int(term.width * 0.4), end="")
    else:
        print(term.move(int(term.height*0.65) + 2, center_text(msg)) + term.color_rgb(*hex_to_rgb(colors.error)) + term.on_color_rgb(*hex_to_rgb(colors.div)) + msg, end="")

def display_success(msg):
    display_error(None)
    if not msg:
        print(term.move(int(term.height*0.65) + 2, int(term.width * 0.3)) + term.on_color_rgb(*hex_to_rgb(colors.div)) + " " * int(term.width * 0.4), end="")
    else:
        print(term.move(int(term.height*0.65) + 2, center_text(msg)) + term.color_rgb(*hex_to_rgb(colors.success)) + term.on_color_rgb(*hex_to_rgb(colors.div)) + msg, end="", flush=True)
        sys.stdout.flush()

def handle_submit():
    global error_show, code, user_token
    if len(code) != 6:
        msg = "Join code missing"
        display_error(msg)
        error_show = True
        return False
    
    try:
        resp = requests.post(f"https://{config.HOST}:{config.PORT}/api/invites/join", json={"user_token": user_token, "invite_code": code})
    except Exception as e:
        display_error("Could not join server")
        error_show = True
        return False
    if resp.status_code == 200:
        
        data = resp.json()
        return data["server_id"]
    elif resp.status_code == 403:
        display_error("Invalid credentials")
        error_show = True
        return False
    elif resp.status_code == 500:
        display_error("Server error: " + resp.json()["message"])
        error_show = True
        return False
    elif resp.status_code == 400:
        display_error("Invalid code")
        error_show = True
        return False

def redraw_all():
    print(term.clear())
    draw_background()
    draw_menu()
    draw_all_text()
    draw_fields()
    draw_buttons()  
    print("")

def main(token):
    global code, user_token, selection, error_show
    user_token = token
    cursor.hide()
    

    redraw_all()
    
    

    with term.cbreak():
        val = ""
        while True:
            sx = term.width
            sy = term.height
            val = term.inkey(timeout=0.01)
            if not val:
                if term.width != sx or term.height != sy:
                    redraw_all()
                continue
            
            if val.code == term.KEY_ESCAPE:
                return None
            if val.code == term.KEY_ENTER and selection == 1:
                ret = handle_submit()
                if ret:
                    return ret
            if repr(val) in keyshortcuts.back_keys:
                selection = max(0, selection - 1)
                draw_fields()
                draw_buttons()
                print("")
            elif repr(val) in keyshortcuts.next_keys:
                selection = min(1, selection + 1)
                draw_fields()
                draw_buttons()
                print("")
            elif val.code == term.KEY_BACKSPACE:
                if selection == 0:
                    code = code[:-1]
                    
                draw_fields()
                if error_show:
                    display_error(None)
                    error_show = False
                print("")
            elif val.is_sequence:
                pass
            else:
                if selection == 0:
                    code += val
                draw_fields()
                if error_show:
                    display_error(None)
                    error_show = False
            print("")
            if term.width != sx or term.height != sy:
                redraw_all()
