from threads import (reset_chat, add_thread,  retrive_threads, delete_thread, rename_thread)
from utils import ( save_thread, update_thread_title, save_message,load_messages, generate_thread_id, generate_title)
from auth import (create_user, login_user)
from chat import workflow
from langchain_core.messages import AIMessage, HumanMessage,ToolMessage
from streamlit_cookies_manager import EncryptedCookieManager
from turtle import st
from ingest import (ingest_pdf,_THREAD_RETRIEVERS, _THREAD_METADATA, _get_retriever)
cookies = EncryptedCookieManager(
    prefix="myapp",
    password="some-secret-key"
)

if not cookies.ready():
    st.stop()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = cookies.get("logged_in") == "true"

if "username" not in st.session_state:
    st.session_state.username = cookies.get("username")

if cookies.get("logged_in") == "true":
    st.session_state.logged_in = True
    st.session_state.username = cookies.get("username")


def show_auth():
    st.markdown(
            "<h4 style='text-align:center; color:gray;'>Welcome</h4>",
            unsafe_allow_html=True
            )
    st.title("My Chatbot")

    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Signup"])

        # -------- SIGNUP --------
        with tab2:

            email = st.text_input("Email", key="signup_email")

            username = st.text_input("Username", key="signup_user")

            password = st.text_input(
                "Password",
                type="password",
                key="signup_pass"
            )

            if st.button("Create Account"):

                if not email or not username or not password:

                    st.warning("All fields are required")

                elif "@" not in email:

                    st.warning("Enter a valid email")

                elif len(username) < 3:

                    st.warning("Username must be at least 3 characters")

                elif " " in username:

                    st.warning("Username cannot contain spaces")

                elif len(password) < 6:

                    st.warning("Password must be at least 6 characters")

                else:

                    result = create_user(
                        email,
                        username,
                        password
                    )

                    if result == "success":

                        st.success(
                            "Account created successfully! Please login."
                        )

                    elif result == "email_exists":

                        st.error("Email already exists")

                    elif result == "username_exists":

                        st.error("Username already taken")

                    else:

                        st.error("Something went wrong")

        # -------- LOGIN --------
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")

            if st.button("Login"):
                user = login_user(email, password)

                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]  

                    st.session_state['chat_threads'] = retrive_threads(st.session_state.username)

                    cookies["logged_in"] = "true"
                    cookies["email"] = email
                    cookies["username"] = user["username"]
                    cookies.save()

                    st.rerun()
                
                else:
                    st.error("Invalid credentials")

# -------------------------------------------------------showApp------------------------------------------------------------

def show_app():   
    #----------------------------------------------page title------------------------------------------------------
    st.title("My Chatbot")
    #--------------------------------------------------Session Setup-----------------------------------------------
    # initialize message history in session state 
    if "message_history" not in st.session_state:
        st.session_state['message_history'] = []

    if 'thread_id' not in st.session_state:
        st.session_state['thread_id'] = generate_thread_id()

    if "ingested_docs" not in st.session_state:
        st.session_state["ingested_docs"] = {}
        

    # if 'chat_threads' not in st.session_state:
    #     st.session_state['chat_threads'] = retrive_threads(username=st.session_state.username)
    # add_threads(st.session_state['thread_id'])
    # if 'chat_threads' not in st.session_state:
    #     if st.session_state.get("logged_in") and st.session_state.get("username"):
    #         st.session_state['chat_threads'] = retrive_threads(st.session_state.username)
    #     else:
    #         st.session_state['chat_threads'] = []
    # if st.session_state.logged_in and st.session_state.username:

    #     st.session_state['chat_threads'] = retrive_threads(
    #         st.session_state.username
    #     )

    # else:
    #     st.session_state['chat_threads'] = []
    # add_threads(st.session_state['thread_id'])

    # if "ingested_docs" not in st.session_state:
    #     st.session_state["ingested_docs"] = {}
    # add_thread(st.session_state["thread_id"])
    # Always load chats fresh from database
    if st.session_state.logged_in and st.session_state.username:

        st.session_state['chat_threads'] = retrive_threads(
            st.session_state.username
        )
    else:
        st.session_state['chat_threads'] = []
    add_thread(st.session_state["thread_id"])

    thread_key = str(st.session_state["thread_id"])
    thread_docs = st.session_state["ingested_docs"].setdefault(thread_key, {})
    threads = st.session_state["chat_threads"][::-1]
    selected_thread = None

# ----------------------------------------------------------- ACTIVE PDF INFO -------------------------------------------------------

    if thread_docs:

        latest_doc = list(thread_docs.values())[-1]

        st.info(
            f"📄 Document Attached: {latest_doc.get('filename')}"
        )



    #--------------------------------------------------sidebar UI----------------------------------------------------
    if st.session_state.logged_in:

        with st.sidebar:
            st.markdown(f"### 👤 {st.session_state.username}")

            # if st.button("Logout"):
            #     st.session_state.logged_in = False
            #     st.session_state.username = None

            #     # 🔥 CLEAR OLD USER DATA
            #     st.session_state['chat_threads'] = []
            #     st.session_state['message_history'] = []
            #     st.session_state['thread_id'] = None

            #     cookies["logged_in"] = "false"
            #     cookies["email"] = ""
                
            #     cookies.save()

            #     st.rerun()
            if st.button("Logout"):

                st.session_state.logged_in = False
                st.session_state.username = None

                if 'chat_threads' in st.session_state:
                    del st.session_state['chat_threads']

                if 'last_user' in st.session_state:
                    del st.session_state['last_user']

                st.session_state['message_history'] = []
                st.session_state['thread_id'] = None


                cookies["logged_in"] = "false"
                cookies["email"] = ""

                cookies.save()

                st.rerun()

            if st.button('New Chat'):
                reset_chat()


# -----------------------------------------------------------------------------------------------------------------------------------------------
            st.markdown("---")

            if thread_docs:
                latest_doc = list(thread_docs.values())[-1]
                st.sidebar.success(
                    f"Using `{latest_doc.get('filename')}` "
                    f"({latest_doc.get('chunks')} chunks from {latest_doc.get('documents')} pages)"
                )
                st.sidebar.markdown("### Uploaded Documents")

            else:
                st.sidebar.info("No PDF indexed yet.")

            uploaded_pdf = st.sidebar.file_uploader("Upload a PDF for this chat",type=["pdf"])

            # ---------------- REMOVE DOCUMENT STATE ----------------
            if uploaded_pdf is None:

                if thread_key in st.session_state["ingested_docs"]:
                    del st.session_state["ingested_docs"][thread_key]

                if thread_key in _THREAD_RETRIEVERS:
                    del _THREAD_RETRIEVERS[thread_key]

                if thread_key in _THREAD_METADATA:
                    del _THREAD_METADATA[thread_key]

            if uploaded_pdf:

                # SAVE THREAD FIRST
                if st.session_state['thread_id'] not in st.session_state['chat_threads']:

                    # save_thread(st.session_state['thread_id'],st.session_state.username,generate_title(st.session_state['thread_id']))

                    st.session_state['chat_threads'].append(
                        st.session_state['thread_id']
                    )

                if uploaded_pdf.name in thread_docs:

                    st.sidebar.info(
                        f"`{uploaded_pdf.name}` already processed for this chat."
                    )

                else:

                    with st.sidebar.status("Indexing PDF…",expanded=True)as status_box:

                        summary = ingest_pdf(
                            uploaded_pdf.getvalue(),
                            thread_id=thread_key,
                            filename=uploaded_pdf.name,
                        )

                        thread_docs[uploaded_pdf.name] = summary

                        status_box.update(
                            label="✅ PDF indexed",
                            state="complete",
                            expanded=False
                        )

                    st.rerun()
   


            # if thread_docs:
            #     latest_doc = list(thread_docs.values())[-1]
            #     st.sidebar.success(
            #         f"Using `{latest_doc.get('filename')}` "
            #         f"({latest_doc.get('chunks')} chunks from {latest_doc.get('documents')} pages)"
            #     )
            # else:
            #     st.sidebar.info("No PDF indexed yet.")

            # uploaded_pdf = st.sidebar.file_uploader("Upload a PDF for this chat", type=["pdf"])
            # if uploaded_pdf:
            #     if uploaded_pdf.name in thread_docs:
            #         st.sidebar.info(f"`{uploaded_pdf.name}` already processed for this chat.")
            #     else:
            #         with st.sidebar.status("Indexing PDF…", expanded=True) as status_box:
            #             summary = ingest_pdf(
            #                 uploaded_pdf.getvalue(),
            #                 thread_id=thread_key,
            #                 filename=uploaded_pdf.name,
            #             )
            #             thread_docs[uploaded_pdf.name] = summary
            #             status_box.update(label="✅ PDF indexed", state="complete", expanded=False)

            st.markdown("---")
# -----------------------------------------------------------------------------------------------------------------------------------------------

            st.session_state['chat_threads'] = retrive_threads(st.session_state.username)


            st.sidebar.subheader('My Chats')
                
            for thread_id in st.session_state['chat_threads']:
                # [::-1]:
                
                    col1, col2 = st.columns([4, 1])
                    messages = load_messages(thread_id)

                    if len(messages) > 0:
                    # check = load_conversation(thread_id)
                    # if check and hasattr(check, "values") and 'messages' in check.values and len(check.values['messages']) > 0:
                        snap = generate_title(thread_id)
                        if snap and snap != "new chat":
                            update_thread_title(thread_id, snap)

                        with st.sidebar.container():
                        # with col1:
                        #     if st.button(f"{snap} ....", key=thread_id):
                        #         st.session_state['thread_id']= thread_id
                                    
                        #         # old_chat = load_conversation(thread_id)
                        #         # state = load_conversation(thread_id)
                        #         # old_chat = state.values.get("messages", [])
                        #         old_chat = load_messages(thread_id)
                        #         temp_message = []

                        #         # for msg in old_chat:
                        #         #     if isinstance(msg, HumanMessage):
                        #         #         role = 'user'
                        #         #     else:
                        #         #         role = 'assistant'
                        #         #     temp_message.append({'role': role, 'content': msg.content})
                        #         for msg in old_chat:
                        #             # skip tool outputs completely
                        #             if isinstance(msg, ToolMessage):
                        #                 continue

                        #             if isinstance(msg, HumanMessage):

                        #                 temp_message.append({
                        #                     'role': 'user',
                        #                     'content': msg.content
                        #                 })

                        #             elif isinstance(msg, AIMessage):

                        #                 # skip empty/tool-call AI messages
                        #                 if not msg.content:
                        #                     continue

                        #                 # skip raw dict/json outputs
                        #                 if isinstance(msg.content, str):

                        #                     if (
                        #                         msg.content.startswith("{")
                        #                         and "context" in msg.content
                        #                     ):
                        #                         continue

                        #                 temp_message.append({
                        #                     'role': 'assistant',
                        #                     'content': msg.content
                        #                 })
                        #         st.session_state['message_history'] = temp_message
                            with col1:

                                if st.button(f"{snap} ....", key=thread_id):

                                    st.session_state['thread_id'] = thread_id

                                    old_chat = load_messages(thread_id)

                                    temp_message = []

                                    for msg in old_chat:

                                        role = msg["role"]
                                        content = msg["content"]

                                            # skip empty content
                                        if not content:
                                            continue

                                            # skip raw rag json outputs
                                        if(
                                            isinstance(content, str)
                                            and content.startswith("{")
                                            and "context" in content
                                        ):
                                            continue

                                        temp_message.append({
                                            "role": role,
                                            "content": content
                                        })

                                    st.session_state['message_history'] = temp_message

                                    st.rerun()

                            with col2:

                                with st.popover(""):

                                    # ---------------- DELETE ----------------
                                    if st.button("Delete", key=f"del_{thread_id}"):

                                        delete_thread(thread_id)

                                        if thread_id in st.session_state['chat_threads']:
                                            st.session_state['chat_threads'].remove(thread_id)

                                        # if current chat deleted
                                        if st.session_state.get("thread_id") == thread_id:

                                            st.session_state['thread_id'] = generate_thread_id()
                                            st.session_state['message_history'] = []

                                        st.rerun()

                                    # ---------------- RENAME OPEN ----------------
                                    if st.button("Rename", key=f"rename_btn_{thread_id}"):

                                        st.session_state["rename_thread"] = thread_id

                                    # ---------------- RENAME INPUT ----------------
                                    if st.session_state.get("rename_thread") == thread_id:

                                        new_name = st.text_input(
                                            "New Chat Name",
                                            key=f"rename_input_{thread_id}"
                                        )

                                        if st.button("Save", key=f"save_{thread_id}"):

                                            rename_thread(thread_id, new_name)

                                            del st.session_state["rename_thread"]

                                            st.rerun()

    #---------------------------------------------Main UI-------------------------------------------------

    # loading the massages/conversation history from the session state and displaying them in the chat interface.
    for message in st.session_state['message_history']:
        with st.chat_message(message['role']):
            st.text(message['content'])

    # taking user input from the chat input box and processing it. When the user types a message and submits it
    chat_box=st.chat_input('Type Here')

    if chat_box:
        if st.session_state['thread_id'] not in st.session_state['chat_threads']:
            save_thread(st.session_state['thread_id'],st.session_state.username,generate_title(st.session_state['thread_id']))
            st.session_state['chat_threads'].append(st.session_state['thread_id'])

        # when the user submits a message, we append it to the message history in the session state and display it in the chat interface. 
        st.session_state['message_history'].append({'role': 'user' , 'content' : chat_box})
        save_message(
            st.session_state['thread_id'],
            'user',
            chat_box
)
        with st.chat_message('user'):
            st.text(chat_box)

        # CONFIG =({'configurable' : {'thread_id' : st.session_state['thread_id']}})
        CONFIG = {
            'configurable' : {'thread_id' : st.session_state['thread_id'],'user': st.session_state.username},
            'metadata' : {
                'thread_id' : st.session_state['thread_id']
            },
            'run_name' : 'chat_turn'
        }
    

        with st.chat_message("assistant"):
        # 🔹 Show thinking message first (UX improvement)
            thinking_placeholder = st.empty()
            thinking_placeholder.write("🔍 Fetching latest data...")

            def stream_response():
                started = False
                for message_chunk, metadata in workflow.stream(
                    {"messages": [HumanMessage(content=chat_box)]},
                    config=CONFIG,
                    stream_mode="messages"
                ):
                    if isinstance(message_chunk, AIMessage):
                        content = message_chunk.content

                        # skip anything that looks like tool/system output
                        if not content:
                            continue

                        if "<function=" in content or "{" in content and "query" in content:
                            continue

                        if not started:
                            thinking_placeholder.empty()
                            started = True

                        yield content

                thinking_placeholder.empty()
                        


            # ✅ Stream final cleaned response
            ai_message = st.write_stream(stream_response())
            save_message(
                st.session_state['thread_id'],
                'assistant',
                ai_message
            )

        
    
        # ✅ Save chat history
        st.session_state["message_history"].append({"role": "assistant", "content": ai_message})



if not st.session_state.logged_in:
    show_auth()
else:
    show_app()