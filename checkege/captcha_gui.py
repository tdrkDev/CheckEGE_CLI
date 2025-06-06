import tkinter as tk
import tkinter.messagebox as mbox
from PIL import Image, ImageTk
import io

class CaptchaGUI:
    def __init__(self):
        self.image = None
        self.window = None
        self.canvas = None
        self.entry = None
        self.token = None

    def set_captcha(self, image: bytes):
        self.image = image

    def solve(self) -> int:
        self.window = tk.Tk()
        self.window.title("Необходимо решить капчу")

        self.canvas = tk.Canvas(self.window, width=300, height=100)
        self.canvas.pack()

        # Load image into canvas
        self.pil_image = Image.open(io.BytesIO(self.image))
        self.tk_image = ImageTk.PhotoImage(self.pil_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        # Entry for captcha code
        self.entry = tk.Entry(self.window)
        self.entry.pack()

        # Submit button
        submit_button = tk.Button(self.window, text="Готово", command=self.submit)
        submit_button.pack()

        self.window.mainloop()
        return self.code

    def submit(self):
        code = self.entry.get().strip()        
        if len(code) != 6:
            mbox.showerror("Ошибка", "Капча должна быть из 6 символов.")
            return
        
        if not code.isnumeric():
            mbox.showerror("Ошибка", "Капча должна содержать только цифры.")
            return
        
        self.code = int(code)
        self.window.destroy()
