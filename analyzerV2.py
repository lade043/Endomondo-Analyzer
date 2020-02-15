import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import requests
from scipy.signal import medfilt
from copy import deepcopy
from json import loads

import numpy as np

with open('endomondo.config', 'r') as conf:
    username = conf.readline()[:-1]
    password = conf.readline()


class Requester:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.session()
        self.cookies = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.endomondo.com/home',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers',
        }
        self.data = '{"email":"' + self.email + '","password":"' + self.password + '","remember":true}'

    def login(self):
        # getting csrf token, jsessionid and awselb
        response = self.session.get('https://www.endomondo.com/', headers=self.headers, cookies=self.cookies)
        self.headers["X-CSRF-TOKEN"] = response.cookies["CSRF_TOKEN"]
        self.headers["Referer"] = "https://www.endomondo.com/login"
        self.headers["Origin"] = "https://www.endomondo.com"
        self.headers["Content-Type"] = "application/json;charset=utf-8"
        response2 = self.session.post('https://www.endomondo.com/rest/session', headers=self.headers,
                                      cookies=self.cookies, data=self.data)

    def get_workout(self, url):
        self.headers["Referer"] = url
        response = self.session.get("https://www.endomondo.com/rest/v1/" + url[26:], headers=self.headers,
                                    cookies=self.cookies)
        return response.content.decode('utf-8')


class Training:
    class Plot:
        def __init__(self, data, y_label, line_color):
            self.raw_data = data
            self.data = data
            self.y_label = y_label
            self.line_color = line_color
            self.visible = True
            self.inherited = None

        def set_visible(self, boolean):
            self.visible = boolean

        def average(self, _i):
            self.data = medfilt(self.raw_data, _i)

    def __init__(self, json, line_type):
        self.decoded = loads(json)
        self.line_type = line_type
        self.name = self.decoded['id']

        # creating all plots
        heart_rate = []
        for i in range(len(self.decoded['points']['points'])):
            if "heart_rate" in self.decoded['points']['points'][i]['sensor_data']:
                heart_rate.append(self.decoded['points']['points'][i]['sensor_data']['heart_rate'])
            else:
                if heart_rate:
                    heart_rate.append(heart_rate[-1])
                else:
                    heart_rate.append(0)
        self.plot_heart_rate = self.Plot(heart_rate, "[heart rate] = bpm", 'tab:red')

        self.distance = [self.decoded["points"]["points"][i]["distance"]
                         for i in range(len(self. decoded['points']['points']))]

        speed = []
        for i in range(len(self.decoded['points']['points'])):
            if "speed" in self.decoded['points']['points'][i]['sensor_data']:
                speed.append(self.decoded['points']['points'][i]['sensor_data']['speed'])
            else:
                if speed:
                    speed.append(speed[-1])
                else:
                    speed.append(0)
        avg = np.average(speed)
        for j, i in enumerate(speed):
            try:
                speed[j] = 60 / i
            except ZeroDivisionError:
                speed[j] = 60 / avg
        self.plot_speed = self.Plot(speed, "[speed] = minpkm", 'tab:blue')

        alt = []
        for i in range(len(self.decoded['points']['points'])):
            if "altitude" in self.decoded['points']['points'][i]:
                alt.append(self.decoded['points']['points'][i]['altitude'])
            else:
                if alt:
                    alt.append(alt[-1])
                else:
                    alt.append(None)
        for j, i in enumerate(alt):
            if i is None:
                for el in alt[j:]:
                    if el:
                        alt[j] = el
        self.plot_altitude = self.Plot(alt, "[altitude] = m", 'tab:green')
        self.plot_speed.inherited = [self.distance, self.line_type, self.name]
        self.plot_altitude.inherited = [self.distance, self.line_type, self.name]
        self.plot_heart_rate.inherited = [self.distance, self.line_type, self.name]
        self.date = self.decoded["local_start_time"]
        self.empty_plot = self.Plot([0 for _ in range(len(self.decoded['points']['points']))], "", "tab:blue")
        self.empty_plot.set_visible(False)
        self.empty_plot.inherited = [self.distance, self.line_type, self.name]


def txt_changed_0(txt):
    if len(txt) >= 50:
        Trainings[0] = Training(user.get_workout(txt), '-')
    plot(states)


def txt_changed_1(txt):
    if not txt:
        Trainings.pop(1)
    if len(txt) >= 50:
        if len(Trainings) >= 2:
            Trainings[1] = Training(user.get_workout(txt), '--')
        else:
            Trainings.append(Training(user.get_workout(txt), '--'))
    plot(states)


def txt_changed_2(txt):
    if not txt:
        Trainings.pop(2)
    if len(txt) >= 50:
        if len(Trainings) >= 3:
            Trainings[2] = Training(user.get_workout(txt), ':')
        else:
            Trainings.append(Training(user.get_workout(txt), ':'))
    plot(states)


def txt_changed_3(txt):
    if not txt:
        Trainings.pop(3)
    if len(txt) >= 50:
        if len(Trainings) >= 4:
            Trainings[3] = Training(user.get_workout(txt), '-.')
        else:
            Trainings.append(Training(user.get_workout(txt), '-.'))
    plot(states)


def slide(numb):
    numb = int(numb)
    for training in Trainings:
        training.plot_speed.average(numb)
        training.plot_heart_rate.average(numb)
    plot(states)


def slide_change(n):
    n = int(n)
    if not n % 2:
        slider.set(n + 1)


def btn_slide():
    slide(int(slider.get()))


def check_box():
    global states
    states['plot_speed'] = varSpeed.get()
    states['plot_altitude'] = varAltitude.get()
    states['plot_heart_rate'] = varHeart.get()
    plot(states)


def submit():
    global txtBoxes
    temp = [txtBox0.get(), txtBox1.get(), txtBox2.get(), txtBox3.get()]
    for i, element in enumerate(temp):
        if not element == txtBoxes[i]:
            if i == 0:
                txt_changed_0(element)
            if i == 1:
                txt_changed_1(element)
            if i == 2:
                txt_changed_2(element)
            if i == 3:
                txt_changed_3(element)
            txtBoxes[i] = element


user = Requester(username, password)
user.login()
Trainings = [Training(user.get_workout("https://www.endomondo.com/users/19154541/workouts/1458780940"), '-')]


states = {'plot_speed': True, 'plot_altitude': True, 'plot_heart_rate': False}

txtBoxes = ['', '', '', '']

root = tkinter.Tk()
root.wm_title("Endomondo Analyzer")

fig = Figure(figsize=(5, 4), dpi=100)
fig.add_subplot(111)
ax1 = fig.subplots()
ax2 = ax1.twinx()

canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

txtBox0 = tkinter.Entry(root)
txtBox0.place(x=20, y=40)
lbl0 = tkinter.Label(root, text="durchgezogen")
lbl0.place(x=200, y=40)
lbl1 = tkinter.Label(root, text="gestrichelt")
lbl1.place(x=200, y=80)
lbl0 = tkinter.Label(root, text="gepunktet")
lbl0.place(x=200, y=120)
lbl1 = tkinter.Label(root, text="gestrichpunktet")
lbl1.place(x=200, y=160)
txtBox1 = tkinter.Entry(root)
txtBox1.place(x=20, y=80)
txtBox2 = tkinter.Entry(root)
txtBox2.place(x=20, y=120)
txtBox3 = tkinter.Entry(root)
txtBox3.place(x=20, y=160)


slider = tkinter.Scale(root, from_=1, to=35, orient=tkinter.HORIZONTAL, length=300, command=slide_change)
slider.place(x=20, y=250)

varSpeed = tkinter.BooleanVar()
chckSpeed = tkinter.Checkbutton(root, text="Speed", command=check_box, variable=varSpeed)
chckSpeed.place(x=20, y=410)
chckSpeed.select()
varAltitude = tkinter.BooleanVar()
chckAltitude = tkinter.Checkbutton(root, text="Altitude", command=check_box, variable=varAltitude)
chckAltitude.place(x=20, y=450)
chckAltitude.select()
varHeart = tkinter.BooleanVar()
chckHeart = tkinter.Checkbutton(root, text="Heart Rate", command=check_box, variable=varHeart)
chckHeart.place(x=20, y=490)

btnSubmit = tkinter.Button(root, command=submit, text="Submit")
btnSubmit.place(x=20, y=200)


btnChangeScale = tkinter.Button(root, command=btn_slide, text="Change Average")
btnChangeScale.place(x=20, y=290)

Dates = tkinter.StringVar(root)
lblDates = tkinter.Label(root, textvariable=Dates)
lblDates.place(x=20, y=550)


def _quit():
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate


def plot(_dict):
    # choosing which plots to show on which axis
    plot1 = None
    plot2 = None
    dictionary = deepcopy(_dict)
    for element in dictionary:
        if dictionary[element]:
            plot1 = element
            dictionary[element] = 0
            break
    for element in dictionary:
        if dictionary[element]:
            plot2 = element
            dictionary[element] = 0
            break
    global ax1
    global ax2
    color = ""
    ax1.clear()
    ax2.clear()
    # defining lists of plots
    if plot1 == "plot_speed":
        plots1 = [i.plot_speed for i in Trainings]
    elif plot1 == "plot_altitude":
        plots1 = [i.plot_altitude for i in Trainings]
    elif plot1 == "plot_heart_rate":
        plots1 = [i.plot_heart_rate for i in Trainings]
    if plot2 == "plot_altitude":
        plots2 = [i.plot_altitude for i in Trainings]
    elif plot2 == "plot_heart_rate":
        plots2 = [i.plot_heart_rate for i in Trainings]
    if plot1 is None:
        plots1 = [Trainings[0].empty_plot]
    if plot2 is None:
        plots2 = [Trainings[0].empty_plot]
    color = plots1[0].line_color
    ax1.set_xlabel('[distance] = km')
    ax1.set_ylabel(plots1[0].y_label, color=color)
    dates = "Dates:\n"
    for training in Trainings:
        dates = dates + training.date[:10] + "\n"
    Dates.set(dates)

    for pl in plots1:
        ax1.plot(pl.inherited[0], pl.data, color=color, visible=pl.visible, linestyle=pl.inherited[1])
    ax1.tick_params(axis='y', labelcolor=color)
    color = plots2[0].line_color
    ax2.set_xlabel('[distance] = km')
    ax2.set_ylabel(plots2[0].y_label, color=color)

    for pl in plots2:
        ax2.plot(pl.inherited[0], pl.data, color=color, visible=pl.visible, linestyle=pl.inherited[1])
    ax2.tick_params(axis='y', labelcolor=color)
    fig.subplots_adjust(left=0.2)
    fig.canvas.draw_idle()


plot(states)
fig.canvas.draw_idle()
button = tkinter.Button(master=root, text="Quit", command=_quit)
button.pack(side=tkinter.BOTTOM)

tkinter.mainloop()