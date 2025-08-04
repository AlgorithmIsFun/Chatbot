import os
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from PIL import Image, ImageTk, ImageSequence, ImageEnhance
import subprocess
import threading
from win11toast import toast
from pathlib import Path
import ctypes
import time
myappid = 'ak.chatbot'  # This should be a unique string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
chat_box = None
switch = 0
chat_name = ""
def read_from_process():
    """Read output from background process and update chat box"""
    global chat_box
    while True:
        line = process.stdout.readline()
        print(line)
        if not line:
            break
        if chat_box:
            chat_box.config(state=tk.NORMAL)
            chat_box.insert(tk.END, f"ChatBot: {line}")
            chat_box.config(state=tk.DISABLED)
            chat_box.see(tk.END)

        if "Models Loaded." in line:
            global switch
            switch = 1
            toast("Chatbot", "Model loaded successfully!")


# Start background script with pipes
process = subprocess.Popen(
    ["python", "secondary.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1
)
if process.poll() is not None:
    exit(1)
threading.Thread(target=read_from_process, daemon=True).start()

def main_window():
    def send_message(event=None):
        global chat_box, chat_name
        message = entry.get().strip()
        if message:
            chat_box.config(state=tk.NORMAL)
            chat_box.insert(tk.END, f"You: {message}\n")
            chat_box.config(state=tk.DISABLED)
            chat_box.see(tk.END)
            process.stdin.write(message + "\n")
            process.stdin.flush()
            file_path = "chats\\{}.txt".format(chat_name)
            with open(file_path, "a") as file:
                file.write(message + "\n")
            entry.delete(0, tk.END)


    # Main window
    root = tk.Tk()
    root.title("Image + Chatbox UI")
    root.geometry("800x500")
    root.configure(bg="white")
    root.iconbitmap("green-circle.ico")
    # Create a container frame for sidebar + main content
    main_frame = tk.Frame(root)
    main_frame.pack(side="left", fill="y", expand=True)
    # Create sidebar frame
    sidebar = tk.Frame(main_frame, width=200, bg="#2c3e50")
    sidebar.pack(side="left", fill="y")
    # Load image
    image = Image.open("blue_circle.gif")  # Change to your image file
    #image = image.resize((600, 300), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(image)
    frames = []

    # Extract frames from GIF
    try:
        while True:
            frame = image.copy().resize((60, 30))
            frames.append(ImageTk.PhotoImage(frame))
            image.seek(len(frames))  # Go to next frame
    except EOFError:
        pass  # No more frames
    # Image label
    image_label = tk.Label(sidebar, image=photo)
    image_label.pack(side="top", anchor="nw", padx=0, pady=0)

    sidebar_visible = True
    def toggle_sidebar(event=None):
        nonlocal sidebar_visible
        if sidebar_visible:
            sidebar.pack_forget()  # Hide sidebar
            toggle_button.config(text=">>")  # Change toggle button text
            sidebar_visible = False
        else:
            sidebar.pack(side="left", fill="y")  # Show sidebar
            sidebar.lift()
            toggle_button.config(text="<<")
            sidebar_visible = True

    toggle_button = tk.Button(root, text="<<", bg="white", fg="black", command=toggle_sidebar)
    toggle_button.pack(side="top", anchor="nw", padx=0, pady=0)

    def new_chat():
        for i in range(20):
            file_path = "chats\\chat{}.txt".format(i)
            if not os.path.exists(file_path):
                global chat_name
                open(file_path, "w").close()
                nonlocal listbox
                path = Path(file_path)
                chat_name = path.stem
                if chat_name not in listbox.get(0, tk.END):  # Prevent duplicates
                    listbox.insert(tk.END, chat_name)
                listbox.selection_clear(0, tk.END)
                items = [
                    os.path.splitext(f)[0]  # remove .txt extension
                    for f in os.listdir("chats")
                    if f.endswith(".txt")
                ]
                index = items.index(chat_name)
                listbox.selection_set(index)
                listbox.selection_set(index)  # Select the item
                listbox.activate(index)  # Make it active (optional)
                listbox.see(index)
                return
        print("No new chat can be created.")

    newchat_button = tk.Button(sidebar, text="New Chat", bg="white", fg="black", command=new_chat)
    newchat_button.pack(side="top")

    def open_apps(event=None):
        print("In development")
    apps_button = tk.Button(sidebar, text="Other Apps", bg="white", fg="black", command=open_apps)
    apps_button.pack(side="top")

    def on_select(event):
        global chat_name
        selected = listbox.get(listbox.curselection())
        chatfile = "chats\\" + selected + ".txt"
        chat_name = selected
        with open(chatfile, "r") as file:
            global chat_box
            chat_box.config(state=tk.NORMAL)
            chat_box.delete("1.0", tk.END)
            for line in file:
                chat_box.insert(tk.END, line)
            chat_box.config(state=tk.DISABLED)

    # Create a Listbox
    listbox = tk.Listbox(sidebar)
    listbox.pack(side="top")
    items = [
        os.path.splitext(f)[0]  # remove .txt extension
        for f in os.listdir("chats")
        if f.endswith(".txt")
    ]
    # Add items
    for item in items:
        listbox.insert(tk.END, item)

    def show_context_menu(event):
        # Select the item under the mouse before showing menu
        index = listbox.nearest(event.y)
        if index >= 0:
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(index)
            listbox.activate(index)
            context_menu.post(event.x_root, event.y_root)  # Show menu at mouse position

    def share_item():
        selected = listbox.get(listbox.curselection())
        if selected:
            print(f"Sharing {selected}")

    def rename_item():
        selected = listbox.get(listbox.curselection())
        if selected:
            new_name = simpledialog.askstring("Rename", f"Enter new name for {selected}:")
            if new_name:
                index = listbox.curselection()[0]
                listbox.delete(index)
                listbox.insert(index, new_name)
                old_filename = f"chats/{selected}.txt"
                new_filename = f"chats/{new_name}.txt"
                os.rename(old_filename, new_filename)

    def delete_item():
        selected = listbox.get(listbox.curselection())
        if selected:
            confirm = messagebox.askyesno("Delete", f"Are you sure you want to delete {selected}?")
            if confirm:
                index = listbox.curselection()[0]
                listbox.delete(index)
                filename = f"chats/{selected}.txt"
                if os.path.exists(filename):
                    os.remove(filename)


    # Create context menu
    context_menu = tk.Menu(sidebar, tearoff=0)
    context_menu.add_command(label="Share", command=share_item)
    context_menu.add_command(label="Rename", command=rename_item)
    context_menu.add_command(label="Delete", command=delete_item)

    # Bind event when an item is selected
    listbox.bind("<<ListboxSelect>>", on_select)
    listbox.bind("<Button-3>", show_context_menu)

    def settings(event=None):
        print("In development")

    settings_button = tk.Button(sidebar, text="Settings/Help", bg="white", fg="black", command=settings)
    settings_button.pack(side="bottom")
    global chat_box
    # Chat display
    chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=15, state=tk.DISABLED)
    chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Input area
    frame = tk.Frame(root, bg="white")
    frame.pack(padx=10, pady=5, fill=tk.X)

    entry = tk.Entry(frame, font=("Arial", 12))
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    entry.bind("<Return>", send_message)  # ⬅ Bind Enter key

    def brighten_image(img, factor):
        """Return a brightened version of an image."""
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)

    def on_enter(event):
        img_button.config(image=bright_photo)

    def on_leave(event):
        img_button.config(image=mic_photo)

    button_image = Image.open("images\mic.png")
    button_image = button_image.resize((80, 80))  # Resize if needed
    mic_photo = ImageTk.PhotoImage(button_image)
    bright_photo = ImageTk.PhotoImage(brighten_image(button_image, 1.5))

    def start_listening(event=None):
        print("I need to implement speech to text api from listening.py")

    # Create button with image
    img_button = tk.Button(frame, image=mic_photo, command=start_listening, borderwidth=0, highlightthickness=0)
    img_button.pack(side=tk.RIGHT)

    img_button.bind("<Enter>", on_enter)
    img_button.bind("<Leave>", on_leave)

    frame_index = 0

    def update_frame():
        nonlocal frame_index
        image_label.config(image=frames[frame_index])
        frame_index = (frame_index + 1) % len(frames)
        root.after(10, update_frame)  # Adjust speed (100 ms per frame)

    update_frame()

    root.mainloop()

def loading_screen():
    # Create the main window
    root = tk.Tk()
    root.title("Loading")
    root.geometry("500x400")
    root.resizable(False, False)
    root.config(bg="black")

    # Load GIF
    gif = Image.open("logo_circle.gif")  # <-- replace with your animated GIF

    frames = []
    for frame in ImageSequence.Iterator(gif):
        resized_frame = frame.resize((500, 400), Image.LANCZOS)
        frames.append(ImageTk.PhotoImage(resized_frame))

    # Create label for GIF
    gif_label = tk.Label(root, bg="black")
    gif_label.place(x=0, y=0, relwidth=1, relheight=1)

    frame_index = 0
    stop_animation = False  # Flag to stop GIF safely
    after_id = None
    # Function to animate GIF
    def animate_gif():
        nonlocal frame_index, after_id
        if stop_animation or not gif_label.winfo_exists():
            return  # Stop if window is destroyed
        gif_label.config(image=frames[frame_index])
        frame_index = (frame_index + 1) % len(frames)
        after_id = root.after(10, animate_gif)  # Adjust speed if needed

    # Optional loading text
    loading_label = tk.Label(root, text="Loading...", font=("Arial", 16), fg="white", bg="black")
    loading_label.pack(side="bottom", pady=10)

    # Close after delay (optional)
    def close_after_delay():
        global switch
        while switch == 0:
            time.sleep(0.1)
        nonlocal stop_animation
        stop_animation = True
        loading_label.config(text="Loading Complete", font=("Arial", 16))
        time.sleep(1)  # Show for 5 seconds
        if root.winfo_exists() and after_id:
            root.after_cancel(after_id)
            root.after(0, lambda: (root.destroy(), main_window()))

    animate_gif()
    threading.Thread(target=close_after_delay, daemon=True).start()
    root.mainloop()
loading_screen()