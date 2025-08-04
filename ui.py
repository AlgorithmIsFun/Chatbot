import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk, ImageSequence
import subprocess
import threading
from win11toast import toast
import ctypes
import time
myappid = 'ak.chatbot'  # This should be a unique string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
chat_box = None
switch = 0
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
        global chat_box
        message = entry.get().strip()
        if message:
            chat_box.config(state=tk.NORMAL)
            chat_box.insert(tk.END, f"You: {message}\n")
            chat_box.config(state=tk.DISABLED)
            chat_box.see(tk.END)
            process.stdin.write(message + "\n")
            process.stdin.flush()
            entry.delete(0, tk.END)


    # Main window
    root = tk.Tk()
    root.title("Image + Chatbox UI")
    root.geometry("600x600")
    root.configure(bg="white")
    root.iconbitmap("green-circle.ico")
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
    image_label = tk.Label(root, image=photo)
    image_label.pack(side="top", anchor="nw", padx=0, pady=0)
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

    send_button = tk.Button(frame, text="Send", command=send_message, bg="#007BFF", fg="white")
    send_button.pack(side=tk.RIGHT)

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