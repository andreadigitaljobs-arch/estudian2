
import os

app_path = 'app.py'

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. FIX AUTO-LOGIN CONDITION
# Search for: if not st.session_state['user']:
# Change to: if not st.session_state['user'] and not st.session_state.get('force_logout'):

auto_login_fixed = False
for i, line in enumerate(lines):
    if "if not st.session_state['user']:" in line and "cookie_manager" in "".join(lines[i-5:i+5]): # Ensure it's the auto-login block
        lines[i] = "if not st.session_state['user'] and not st.session_state.get('force_logout'):\n"
        auto_login_fixed = True
        print(f"Fixed Auto-Login Check at line {i+1}")
        break

# 2. FIX LOGOUT BUTTON LOGIC
# Search for: if st.button("Cerrar Sesión", key="logout_btn", use_container_width=True):
# We will replace the indented block following it.

logout_fixed = False
new_logout_logic = [
    "        if st.button(\"Cerrar Sesión\", key=\"logout_btn\", use_container_width=True):\n",
    "            st.session_state['force_logout'] = True # Prevent immediate auto-login loop\n",
    "            st.session_state['user'] = None\n",
    "            if 'supabase_session' in st.session_state: del st.session_state['supabase_session']\n",
    "            try:\n",
    "                cookie_manager.delete(\"supabase_refresh_token\")\n",
    "            except Exception as e: print(f\"Logout cookie error: {e}\")\n",
    "            import time\n",
    "            time.sleep(0.5) # Allow cleanup time\n",
    "            st.rerun()\n"
]

start_logout = -1
end_logout = -1

for i, line in enumerate(lines):
    if "if st.button(\"Cerrar Sesión\", key=\"logout_btn\", use_container_width=True):" in line:
        start_logout = i
        # Find where this block ends. It ends when indentation returns to parent level (8 spaces usually for sidebar inner elements, or 4)
        # The current line probably has 8 spaces indentation.
        current_indent = len(line) - len(line.lstrip())
        
        # Look ahead
        for j in range(i + 1, len(lines)):
            next_line = lines[j]
            if next_line.strip() == "": continue
            next_indent = len(next_line) - len(next_line.lstrip())
            if next_indent <= current_indent:
                end_logout = j
                break
        else:
            end_logout = len(lines)
        break

if start_logout != -1:
    print(f"Replacing Logout Logic at lines {start_logout+1}-{end_logout}")
    lines[start_logout:end_logout] = new_logout_logic
    logout_fixed = True
else:
    print("ERROR: Logout button block not found.")

if auto_login_fixed and logout_fixed:
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("SUCCESS: app.py patched for Logout fix.")
else:
    print("PARTIAL ERROR: Could not find all targets.")

