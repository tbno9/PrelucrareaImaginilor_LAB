import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import struct
import numpy as np
from PIL import Image, ImageTk
import math
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matrice = None
matrice_inversa = None

def read_bmp(file_path):
    with open(file_path, 'rb') as f:
        file_header = f.read(14)
        if len(file_header) < 14:
            raise ValueError("File too small to be a BMP")
        if file_header[0:2] != b'BM':
            raise ValueError("Not a BMP file (invalid signature)")

        data_offset = struct.unpack('<I', file_header[10:14])[0]
        info_header = f.read(40)
        if len(info_header) < 40:
            raise ValueError("Incomplete BMP info header")

        width       = struct.unpack('<i', info_header[4:8])[0]
        height      = struct.unpack('<i', info_header[8:12])[0]
        bit_count   = struct.unpack('<H', info_header[14:16])[0]
        compression = struct.unpack('<I', info_header[16:20])[0]

        bottom_up  = height > 0
        abs_height = abs(height)

        palette = []
        if bit_count == 8:
            f.seek(14 + 40)
            for i in range(256):
                b, g, r, _ = f.read(4)
                palette.append([r, g, b])
        elif bit_count == 4:
            f.seek(14 + 40)
            for i in range(16):
                b, g, r, _ = f.read(4)
                palette.append([r, g, b])

        if bit_count == 24:
            row_size = ((width * 3 + 3) // 4) * 4
        elif bit_count == 32:
            row_size = width * 4
        elif bit_count == 8:
            row_size = ((width + 3) // 4) * 4
        elif bit_count == 4:
            row_size = ((width + 1) // 2 + 3) // 4 * 4
        elif bit_count == 16:
            row_size = ((width * 2 + 3) // 4) * 4
        else:
            raise ValueError(f"Unsupported bit count: {bit_count}")

        f.seek(data_offset)
        pixels = []
        for _ in range(abs_height):
            row_data = f.read(row_size)
            if len(row_data) < row_size:
                raise ValueError("Unexpected end of file")
            row_pixels = []
            if bit_count == 24:
                for x in range(width):
                    b = row_data[x * 3]
                    g = row_data[x * 3 + 1]
                    r = row_data[x * 3 + 2]
                    row_pixels.append([r, g, b])

            elif bit_count == 32:
                for x in range(width):
                    b = row_data[x * 4]
                    g = row_data[x * 4 + 1]
                    r = row_data[x * 4 + 2]
                    row_pixels.append([r, g, b])

            elif bit_count == 8:
                for x in range(width):
                    index = row_data[x]
                    row_pixels.append(palette[index])

            elif bit_count == 4:
                for x in range(width):
                    byte = row_data[x // 2]
                    if x % 2 == 0:
                        index = (byte >> 4) & 0x0F 
                    else:
                        index = byte & 0x0F
                    row_pixels.append(palette[index])

            elif bit_count == 16:
                for x in range(width):
                    pixel = struct.unpack('<H', row_data[x*2:x*2+2])[0]
                    if compression == 3: 
                        r = ((pixel >> 11) & 0x1F) * 255 // 31
                        g = ((pixel >> 5)  & 0x3F) * 255 // 63
                        b = ( pixel        & 0x1F) * 255 // 31
                    else: 
                        r = ((pixel >> 10) & 0x1F) * 255 // 31
                        g = ((pixel >> 5)  & 0x1F) * 255 // 31
                        b = ( pixel        & 0x1F) * 255 // 31
                    row_pixels.append([r, g, b])
                    
            pixels.append(row_pixels)

        if bottom_up:
            pixels.reverse()

        return pixels


def open_image():
    file_path = filedialog.askopenfilename(
        title="Select a BMP Image",
        filetypes=[("BMP files", "*.bmp"), ("All files", "*.*")]
    )

    if not file_path:
        print("No file selected.")
        return

    try:
        global matrice
        matrice = read_bmp(file_path)
        filename = file_path.split("/")[-1]
        status_var.set(f"{filename}")
        afiseaza(matrice, canvas_stanga)
        canvas_dreapta.delete('all')
    except Exception as e:
        print(f"Error: {e}")


# --------------LAB 2-------GRIURI
def grayscale(matrice, varianta_gray):
    rezultat = [] # [[0,1],[0,1],[1,0],[1,0]] = rezultat[[], []]
    for rand in matrice:
        new_rand = []
        for pixel in rand:
            r, g, b = pixel[0], pixel[1], pixel[2]
            if varianta_gray == 1:
                gray = (r + g + b) / 3
            elif varianta_gray == 2:
                gray = 0.299*r + 0.587*g + 0.114*b
            elif varianta_gray == 3:
                gray = min(r,g,b)/2 + max(r,g,b)/2
            new_rand.append([int(gray), int(gray), int(gray)]) # new_rand=[r,g,b]
        rezultat.append(new_rand)
    return rezultat

def conversie_cmyk(matrice):
    rezultat = []
    for rand in matrice:
        new_rand = []
        for pixel in rand:
            r, g, b = pixel[0], pixel[1], pixel[2]
            c=1-(r/255)
            m=1-(g/255)
            y=1-(b/255)
            k=min(c,m,y) #k=black

            if k==1:
                cyan, magenta, yellow = 0, 0, 0 #toata cerneala e in k, pt afisare corecta negru
            else:
                cyan=(c-k)/(1-k)
                magenta=(m-k)/(1-k)
                yellow=(y-k)/(1-k)
            new_rand.append([int(cyan)*255, int(magenta)*255, int(yellow)*255, int(k)*255]) 
        rezultat.append(new_rand)
    return rezultat


#----------LAB 3-----------------

def conversie_yuv(matrice):
    rezultat = []
    for rand in matrice:
        new_rand = []
        for pixel in rand:
            r, g, b = pixel[0], pixel[1], pixel[2]
            
            y = 0.3*r + 0.6*g + 0.1*b # poate fi > 255, de aia fac cu min mai jos
            u = 0.74*(r-y) + 0.27*(b-y) # pot fi negative
            v = 0.48*(r-y) + 0.41*(b-y) # pot fi negative

            new_rand.append([
                #clamp la valori, ca sa nu depaseasca intervalul 0-255
                # max- limiteaza inferior
                # min-limiteaza superior
                int(max(0, min(255, y))), 
                int(max(0, min(255, u + 128))),
                int(max(0, min(255, v + 128)))
            ]) #pt val negative: ex: -10 devine 246
        rezultat.append(new_rand)
    return rezultat


def conversie_ycbcr(matrice):
    rezultat = []
    for rand in matrice:
        new_rand = []
        for pixel in rand:
            r, g, b = pixel[0], pixel[1], pixel[2]
            
            y = 0.299*r + 0.587*g + 0.114*b 
            cb = -0.1687*r - 0.3313*g + 0.498*b + 128
            cr = 0.498*r - 0.4187*g - 0.0813*b + 128

            new_rand.append([
                #clamp la valori, ca sa nu depaseasca intervalul 0-255
                # max- limiteaza inferior
                # min-limiteaza superior
                int(max(0, min(255, y))), 
                int(max(0, min(255, cb))),
                int(max(0, min(255, cr)))
            ])
        rezultat.append(new_rand)
    return rezultat


def conversie_inversa(matrice):
    rezultat = []
    for rand in matrice:
        new_rand = []
        for pixel in rand:
            new_rand.append([255-pixel[0],255-pixel[1],255-pixel[2]])
        rezultat.append(new_rand)
    return rezultat

def calculeaza_canal(matrice,canal):
    rezultat = []
    for rand in matrice:
        new_rand = []
        for pixel in rand:
            p=pixel[canal]            
            if canal==0:
                new_rand.append([p,0,0]) #r
            elif canal == 1:
                new_rand.append([0,p,0]) #g
            elif canal == 2:
                new_rand.append([0,0,p]) #b
        rezultat.append(new_rand)
    return rezultat

def afiseaza_inversa(varianta):
    global matrice_inversa
    if varianta == 1:
        if matrice is None:
            return
        matrice_inversa = conversie_inversa(matrice)
        afiseaza(matrice_inversa, canvas_dreapta)
    else:
        if matrice_inversa is None:
            return
        if varianta == 2:
            afiseaza(calculeaza_canal(matrice_inversa, 0), canvas_dreapta)
        elif varianta == 3:
            afiseaza(calculeaza_canal(matrice_inversa, 1), canvas_dreapta) 
        elif varianta == 4:
            afiseaza(calculeaza_canal(matrice_inversa, 2), canvas_dreapta)

def binarizare(matrice, prag=130):
    rezultat = []
    for rand in matrice:
        new_rand=[]
        for pixel in rand:
            medie=int(0.299*pixel[0] + 0.587*pixel[1] + 0.114*pixel[2])
            if medie >= prag:
                culoare = 255 # va fi alb acolo unde media e mai mare decat pragul
            else:
                culoare = 0 # va fi negru, daca intensitatea e mai mica decat pragul
            new_rand.append([culoare, culoare, culoare])
        rezultat.append(new_rand)
    return rezultat

def conversie_hsv(matrice):
    rezultat = []
    for rand in matrice:
        new_rand = []
        for pixel in rand:
            r,g,b = pixel[0]/255.0, pixel[1]/255.0, pixel[2]/255.0
            M=max(r,g,b)
            m=min(r,g,b)
            C=M-m

            V=M

            #SATURATIE
            if(V!=0):
                S=C/V
            else:
                S=0 #negru

            #HUE
            H=0
            if C!=0:
               if M==r: H = 60*(g-b) / C
               elif M == g: H = 120 + 60*(b-r) / C
               elif M == b: H = 240 + 60*(r-g) / C
            if H<0:
                H = H +360

            # normalizare
            h_norm = H * 255/360
            s_norm = S * 255
            v_norm = V * 255
            new_rand.append([h_norm, s_norm, v_norm])
        rezultat.append(new_rand)
    return rezultat

def histograma(matrice):
    curatare_canvas()    # pt ca atunci cand deschid img noua, sa nu ramana histogr veche
    histograma=[0]*256
    for rand in matrice:
        for pixel in rand:
            gray = int((pixel[0] + pixel[1] + pixel[2]) / 3)
            histograma[gray] += 1

    #desenare grafic - cat de des e intalnita o intensitate
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(range(256), histograma, color='pink', width=1, edgecolor='none')
    ax.set_xlim(0, 255)

    canvas_mpl = FigureCanvasTkAgg(fig, master=sectiune_analiza)
    canvas_mpl.draw()
    canvas_mpl.get_tk_widget().pack(fill="both", expand=True)
    plt.close(fig)

def calcul_momente(matrice):
    #ordin 1
    suma_intensitate = 0
    sumax_intensitate = 0
    sumay_intensitate = 0
    for y, rand in enumerate(matrice):
        for x, pixel in enumerate(rand):
            r, g, b = pixel[0], pixel[1], pixel[2]
            intensitate = 0.299*r + 0.587*g + 0.114*b  #gri-ul
            suma_intensitate += intensitate
            sumax_intensitate += x * intensitate
            sumay_intensitate += y * intensitate
    
    m_x = sumax_intensitate / suma_intensitate
    m_y = sumay_intensitate / suma_intensitate

    #ordin 2
    sumaxx = 0
    sumayy = 0
    sumaxy = 0
    for y,rand in enumerate(matrice):
        for x, pixel in enumerate(rand):
            r, g, b = pixel[0], pixel[1], pixel[2]
            intensitate = 0.299*r + 0.587*g + 0.114*b #gri-ul
            sumaxx += (x - m_x)**2 * intensitate
            sumayy += (y - m_y)**2 * intensitate
            sumaxy += (x - m_x) * (y - m_y) * intensitate

    M_xx = sumaxx / suma_intensitate
    M_yy = sumayy / suma_intensitate
    M_xy = sumaxy / suma_intensitate
    unghi_rad = 0.5 * math.atan2(2 * M_xy, M_xx - M_yy)
    unghi_grade = math.degrees(unghi_rad)
    return m_x, m_y, M_xx, M_yy, M_xy, unghi_rad, unghi_grade

def afisare_momente():
    if matrice is None: return
    curatare_canvas()
    m_x, m_y, M_xx, M_yy, M_xy, unghi_rad, unghi_grade = calcul_momente(matrice)
    text = tk.Text(sectiune_analiza, font=("Arial", 12))
    text.pack(fill="both", expand=True)
    text.insert("end", f"Centru de masa: m_x = {m_x:.2f}, m_y = {m_y:.2f}\n")
    text.insert("end", f"Momente de ordin 2: M_xx = {M_xx:.2f}, M_yy = {M_yy:.2f}\n")
    text.insert("end", f"Momentul de covarianta: M_xy = {M_xy:.2f}\n")
    text.insert("end", f"Orientare(radiani): {unghi_rad:.2f}\n")
    text.insert("end", f"Orientare(grade): {unghi_grade:.2f}\n")
    text.insert("end", f"\nMatricea de covarianta:\n")
    text.insert("end", f"| {M_xx:.2f}  {M_xy:.2f} |\n")
    text.insert("end", f"| {M_xy:.2f}  {M_yy:.2f} |\n")
    text.config(state="disabled")

def proiectii(matrice_binarizata):  
    curatare_canvas() 
    h = len(matrice_binarizata)
    w = len(matrice_binarizata[0])
    
    proiectie_H = [0] * h
    proiectie_V = [0] * w
    
    for y in range(h):
        for x in range(w):
            if matrice_binarizata[y][x][0] == 255:
                proiectie_H[y] += 1
                proiectie_V[x] += 1
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3))
    ax1.plot(proiectie_H, color='blue')
    ax1.set_title("Proiectie orizontala")

    ax2.plot(proiectie_V, color='red')
    ax2.set_title("Proiectie verticala")

    canvas_mpl = FigureCanvasTkAgg(fig, master=sectiune_analiza)
    canvas_mpl.draw()
    canvas_mpl.get_tk_widget().pack(fill="both", expand=True)
    plt.close(fig)


def curatare_canvas():
    for widget in sectiune_analiza.winfo_children():
        widget.destroy()


def afiseaza(mat, canvas):
    arr = np.array(mat, dtype=np.uint8)
    img = Image.fromarray(arr)
    MAX_W, MAX_H = 600, 600
    img.thumbnail((MAX_W, MAX_H))
    imgtk = ImageTk.PhotoImage(img)
    # canvas.config(width=img.width, height=img.height)
    canvas.create_image(300, 300, anchor="center", image=imgtk)
    canvas.image = imgtk


#=============================INTERFATA
root = tk.Tk()
root.title("Photoshop fake")
w =1200
h=900
root.geometry(f"{w}x{h}")

sectiune_analiza=tk.Frame(root, height=250, bg="#f185e8")
sectiune_analiza.pack(fill="x", padx=5, pady=5)
sectiune_analiza.pack_propagate(False)

sectiune_poza=tk.Frame(root)
sectiune_poza.pack()

canvas_stanga=tk.Canvas(sectiune_poza, width=600, height=600, bg="lightgray")
canvas_stanga.pack(side="left", padx=5, pady=5)

canvas_dreapta=tk.Canvas(sectiune_poza, width=600, height=600, bg="lightgray")
canvas_dreapta.pack(side="left", padx=5, pady=5)

bara_meniu= tk.Menu(root)

# fisier
meniu_file = tk.Menu(bara_meniu, tearoff=0)
meniu_file.add_command(label="Deschide", command=open_image)
bara_meniu.add_cascade(label="Fisier", menu=meniu_file)

#conversii
meniu_conversii=tk.Menu(bara_meniu, tearoff=0)
meniu_conversii.add_command(label="Gri - Media aritmetica", command=lambda: afiseaza(grayscale(matrice, 1), canvas_dreapta))
meniu_conversii.add_command(label="Gri - Luminozitate", command=lambda: afiseaza(grayscale(matrice, 2), canvas_dreapta))
meniu_conversii.add_command(label="Gri - Lightness", command=lambda: afiseaza(grayscale(matrice, 3), canvas_dreapta))
meniu_conversii.add_separator()
meniu_conversii.add_command(label="CMYK", command=lambda: afiseaza(conversie_cmyk(matrice), canvas_dreapta))
meniu_conversii.add_command(label="YUV", command=lambda: afiseaza(conversie_yuv(matrice), canvas_dreapta))
meniu_conversii.add_command(label="YCbCr", command=lambda: afiseaza(conversie_ycbcr(matrice), canvas_dreapta))
meniu_conversii.add_command(label="HSV", command=lambda: afiseaza(conversie_hsv(matrice), canvas_dreapta))
bara_meniu.add_cascade(label="Conversii", menu=meniu_conversii)

# efecte
meniu_efecte = tk.Menu(bara_meniu, tearoff=0)
meniu_efecte.add_command(label="Binarizare", command=lambda: afiseaza(binarizare(matrice), canvas_dreapta))
meniu_inversare = tk.Menu(meniu_efecte, tearoff=0)
meniu_inversare.add_command(label="Afiseaza inversata", command=lambda: afiseaza_inversa(1))
meniu_inversare.add_command(label="Canal R", command=lambda: afiseaza_inversa(2))
meniu_inversare.add_command(label="Canal G", command=lambda: afiseaza_inversa(3))
meniu_inversare.add_command(label="Canal B", command=lambda: afiseaza_inversa(4))

meniu_efecte.add_cascade(label="Inversare", menu=meniu_inversare)
bara_meniu.add_cascade(label="Efecte", menu=meniu_efecte)

# analiza
meniu_analiza = tk.Menu(bara_meniu, tearoff=0)
meniu_analiza.add_command(label="Histograma", command=lambda: histograma(matrice))
meniu_analiza.add_command(label="Momente", command=afisare_momente)
meniu_analiza.add_command(label="Proiectii", command=lambda: proiectii(binarizare(matrice)))
bara_meniu.add_cascade(label="Analiza", menu=meniu_analiza)
root.config(menu=bara_meniu)

status_var = tk.StringVar(value="Nu ai deschis un fisier inca!!!")

status_bar = tk.Label(root, textvariable=status_var, anchor="w")
status_bar.pack(fill="x", side="bottom")

root.mainloop()