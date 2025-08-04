import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import threading
import time
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

    # Function to animate GIF
    def animate_gif():
        nonlocal frame_index
        gif_label.config(image=frames[frame_index])
        frame_index = (frame_index + 1) % len(frames)
        root.after(10, animate_gif)  # Adjust speed if needed

    animate_gif()
    # Optional loading text
    loading_label = tk.Label(root, text="Loading...", font=("Arial", 16), fg="white", bg="black")
    loading_label.pack(side="bottom", pady=10)

    # Close after delay (optional)
    def close_after_delay():
        time.sleep(5)  # Show for 5 seconds
        loading_label.config(text="Loading Complete", font=("Arial", 16))
        time.sleep(1)  # Show for 5 seconds
        root.destroy()
        #show_main_window()

    threading.Thread(target=close_after_delay, daemon=True).start()

    root.mainloop()
loading_screen()