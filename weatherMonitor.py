
from tkinter import *
import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import dates
import json
from datetime import datetime, timedelta

#глобальные переменные для хранения данных из файлов
csv_data = None
json_data = None

#Функция для чтения CSV-файла
def read_csv_file(filename):
    """
    Читает CSV-файл с разделителем ';', пропускает первую строку и преобразует столбец 'Date' в тип datetime.
    Возвращает DataFrame с обработанными данными.
    """
    data = pd.read_csv(filename, sep=';', encoding='cp1251', skiprows=1)  # Чтение файла с нужной кодировкой и пропуском первой строки
    data.columns = data.columns.str.strip()  # Удаление пробелов из названий столбцов
    data['Дата'] = pd.to_datetime(data['Date'])  # Преобразование столбца 'Date' в datetime и создание нового столбца 'Дата'
    return data

#Функция для чтения JSON-файла построчно
def read_json_file(filename):
    """
    Читает JSON-файл, содержащий по одной JSON-записи на строку.
    Объединяет записи в словарь, затем преобразует его в DataFrame.
    Преобразует столбец 'Date' в тип datetime и добавляет столбец 'Дата'.
    """
    with open(filename, 'r', encoding='utf-8') as f:
        data_dict = {}
        for line in f:
            entry = json.loads(line)  #Декодирование каждой строки как JSON
            data_dict.update(entry)  #Объединение всех словарей
    data = pd.DataFrame.from_dict(data_dict, orient='index')  #Преобразование словаря в DataFrame
    data['Дата'] = pd.to_datetime(data['Date'])  #Преобразование в datetime
    return data

#Функция выбора CSV-файла с помощью диалогового окна
def select_csv_file():
    """
    Открывает диалоговое окно для выбора CSV-файла.
    Загружает данные в переменную csv_data, обновляет метки и комбобоксы, отображает диапазон дат.
    """
    global csv_data
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filename:
        csv_data = read_csv_file(filename)
        csv_file_label.config(text=f"Выбран файл CSV: {filename}")
        update_comboboxes(csv_data)

    #Отображение диапазона дат
    start_datetime = csv_data['Дата'].min().strftime('%Y-%m-%d %H:%M:%S')
    end_datetime = csv_data['Дата'].max().strftime('%Y-%m-%d %H:%M:%S')
    date_range_label.config(text=f"Диапазон дат: {start_datetime} - {end_datetime}")

#Функция выбора JSON-файла с помощью диалогового окна
def select_json_file():
    """
    Открывает диалоговое окно для выбора JSON-файла (в формате *.txt).
    Загружает данные в переменную json_data, обновляет метки и комбобоксы, отображает диапазон дат.
    Также размещает комбобокс для выбора прибора.
    """
    global json_data
    filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.txt")])
    if filename:
        json_data = read_json_file(filename)
        json_file_label.config(text=f"Выбран файл JSON: {filename}")
        update_comboboxes(json_data)

    update_comboboxes(json_data)

    #Отображение интерфейса выбора прибора
    device_label = tk.Label(root, text="Выберите прибор")
    device_label.place(x=460, y=5)
    
    device_combobox.place(x=460, y=40)
    device_combobox.bind("<<ComboboxSelected>>", update_y_combobox)
    update_comboboxes(json_data)

    #Отображение диапазона дат
    start_datetime = json_data['Дата'].min().strftime('%Y-%m-%d %H:%M:%S')
    end_datetime = json_data['Дата'].max().strftime('%Y-%m-%d %H:%M:%S')
    date_range_label.config(text=f"Диапазон дат: {start_datetime} - {end_datetime}")

#Комбобоксы
def update_comboboxes(data):
    if csv_data is not None:
        columns = [col for col in data.columns if col not in ['Date', 'RTC_time', 'RTC_date']]
        x_combobox['values'] = ['Дата']  
        y_combobox['values'] = columns
        for y_axis in additional_y_axes:
            y_axis_combobox = root.nametowidget(y_axis._name)  
            y_axis_combobox['values'] = columns
    
    elif json_data is not None:
        unique_devices = set()
        for index, row in data.iterrows():
            device_name = row['uName']
            serial_number = row['serial']
            if serial_number == "01":
                unique_devices.add(device_name)
            else:
                unique_devices.add(f"{device_name} ({serial_number})")

        device_combobox['values'] = list(unique_devices)
        
        y_combobox['values'] = []
        
        for y_axis in additional_y_axes:
            y_axis_combobox = root.nametowidget(y_axis._name) 
            y_axis_combobox['values'] = []
    

def update_y_combobox(event):
    selected_device = device_combobox.get()
    device_name = selected_device.split(" (")[0]  
    serial_number = selected_device.split(" (")[1].replace(")", "") if " (" in selected_device else "01" 
    device_data = json_data[(json_data['uName'] == device_name) & (json_data['serial'] == serial_number)] 
    if selected_device and json_data is not None:
        x_values = []
        for index, row in device_data.iterrows():
            x_values.append(row['Date'])  

        x_combobox['values'] = list(set(x_values))
        y_values = []
        for index, row in device_data.iterrows():
            if 'data' in row:
                y_values.extend(row['data'].keys()) 

        y_combobox['values'] = list(set(y_values))

        for y_axis in additional_y_axes:
            y_axis_combobox = root.nametowidget(y_axis._name)
            y_axis_combobox['values'] = list(set(y_values)) 
        

additional_y_axes = []

def add_y_axis():
    """
    Добавляет новый комбобокс (выпадающий список) для выбора дополнительной Y-оси на графике.
    Размещает его по координате X с учётом уже добавленных комбобоксов.
    Обновляет доступные значения в комбобоксах на основе загруженных данных.
    Если выбран прибор — вызывает обновление данных по выбранному прибору.
    """
    new_y_combobox = ttk.Combobox(root)  #Создаём новый комбобокс
    additional_y_axes.append(new_y_combobox)  #Добавляем его в список дополнительных Y-осей

    #Расчёт позиции по X: сдвигаем каждый следующий комбобокс правее
    new_x_position = 330 + 180 * (len(additional_y_axes) - 0.5)
    new_y_combobox.place(x=new_x_position, y=130)

    #Назначаем обработчик события выбора значения
    new_y_combobox.bind("<<ComboboxSelected>>", update_y_combobox)

    
    update_comboboxes(csv_data if csv_data is not None else json_data)

    #Если выбран прибор — обновляем Y-комбобоксы
    if device_combobox.get():
        update_y_combobox(None)
    else:
        update_comboboxes(csv_data if csv_data is not None else json_data)


def get_min_max(data, x_col, y_col):
    #Инициализируем переменные экстремальными значениями
    min_value, max_value = float('inf'), float('-inf')
    min_data, max_data = None, None
    """
    Возвращает минимальное и максимальное значения Y-оси и соответствующие им даты X-оси.
    
    Аргументы:
    - data: DataFrame с данными
    - x_col: название столбца для X-координаты (обычно 'Дата')
    - y_col: название параметра (столбца), по которому ищем минимум и максимум

    Возвращает:
    - кортежи: (дата, значение) минимума и максимума
    """

    
    if csv_data is not None:
        min_index = data[y_col].idxmin()
        max_index = data[y_col].idxmax()
        min_value = data.loc[min_index, y_col]
        max_value = data.loc[max_index, y_col]
        min_date = data.loc[min_index, x_col]
        max_date = data.loc[max_index, x_col]
        
    if json_data is not None:
        selected_device = device_combobox.get()
        device_name = selected_device.split(" (")[0] 
        serial_number = selected_device.split(" (")[1].replace(")", "") if " (" in selected_device else "01"
        device_data = json_data[(json_data['uName'] == device_name) & (json_data['serial'] == serial_number)] 

        for index, row in device_data.iterrows():
            if 'data' in row and row['data'] is not None:
                if y_col in row['data'] and row['data'][y_col] is not None:
                    current_value = float(row['data'][y_col])
                    if current_value < min_value:
                        min_value = current_value
                        min_data = row  
                    if current_value > max_value:
                        max_value = current_value
                        max_data = row  
        min_date = min_data['Date']
        max_date = max_data['Date']
    if min_data is None or max_data is None:
        return (None, None), (None, None)

    return (min_date, min_value), (max_date, max_value)

def charts():
    x_data = []
    y_data = []

    if csv_data is not None:
        data = csv_data
        start_datetime = data['Дата'].min().strftime('%Y-%m-%d %H:%M:%S')
        end_datetime = data['Дата'].max().strftime('%Y-%m-%d %H:%M:%S')
        data = data[(data['Дата'] >= start_datetime) & (data['Дата'] <= end_datetime)]
        data_resampled = data

        if type_chart.get() != "Без осреднения":
            data.loc[:, 'Дата'] = pd.to_datetime(data['Дата'], errors='coerce')
            if 'Дата' not in data.columns:
                print("Нет столбца 'Дата' в данных.")
                return

            for col in data.columns:
                if col != 'Дата':
                    data.loc[:, col] = pd.to_numeric(data[col], errors='coerce')
            data.set_index('Дата', inplace=True)
            if averaging_chart.get() == "Осреднить за час":
                data_resampled = data.resample('h').mean()
            elif averaging_chart.get() == "Осреднить за 3 часа":
                data_resampled = data.resample('3h').mean()
            elif averaging_chart.get() == "Осреднить за день":
                data_resampled = data.resample('d').mean()
                
            data_resampled.reset_index(inplace=True)

        x_data = data_resampled[axis_x.get()]
        y_data = data_resampled[axis_y.get()]
    elif json_data is not None:
        data = json_data
        start_datetime = data['Дата'].min().strftime('%Y-%m-%d %H:%M:%S')
        end_datetime = data['Дата'].max().strftime('%Y-%m-%d %H:%M:%S')
        data = data[(data['Date'] >= start_datetime) & (data['Date'] <= end_datetime)]
        selected_device = device_combobox.get()
        device_name = selected_device.split(" (")[0]  
        serial_number = selected_device.split(" (")[1].replace(")", "") if " (" in selected_device else "01" 
        device_data = json_data[(json_data['uName'] == device_name) & (json_data['serial'] == serial_number)] 

        device_data.loc[:, 'Дата'] = pd.to_datetime(device_data['Дата'], errors='coerce')
        

        if averaging_chart.get() == "Осреднить за час":
            hourly_data = {}  
            for index, row in device_data.iterrows():
                timestamp = row['Дата']
                hour = timestamp.replace(minute=0, second=0, microsecond=0)  
                if hour not in hourly_data:
                    hourly_data[hour] = {'x': [], 'y': []}
                
                if 'data' in row and axis_y.get() in row['data']:
                    hourly_data[hour]['x'].append(timestamp)
                    hourly_data[hour]['y'].append(float(row['data'][axis_y.get()]))

            for hour, data_values in hourly_data.items():
                if data_values['y']:
                    x_data.append(hour)
                    y_data.append(sum(data_values['y']) / len(data_values['y']))

        if averaging_chart.get() == "Осреднить за 3 часа":
            three_hour_data = {}
            for index, row in device_data.iterrows():
                timestamp = row['Дата']
                three_hour_interval = timestamp.replace(minute=0, second=0, microsecond=0) - timedelta(hours=timestamp.hour % 3)
                if three_hour_interval not in three_hour_data:
                    three_hour_data[three_hour_interval] = {'x': [], 'y': []}
                
                if 'data' in row and axis_y.get() in row['data']:
                    three_hour_data[three_hour_interval]['x'].append(timestamp)
                    three_hour_data[three_hour_interval]['y'].append(float(row['data'][axis_y.get()]))

            for interval, data_values in three_hour_data.items():
                if data_values['y']:
                    x_data.append(interval)
                    y_data.append(sum(data_values['y']) / len(data_values['y']))

        if averaging_chart.get() == "Осреднить за день":
            daily_data = {}
            for index, row in device_data.iterrows():
                timestamp = row['Дата']
                day = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)  
                if day not in daily_data:
                    daily_data[day] = {'x': [], 'y': []}
                
                if 'data' in row and axis_y.get() in row['data']:
                    daily_data[day]['x'].append(timestamp)
                    daily_data[day]['y'].append(float(row['data'][axis_y.get()]))

            for day, data_values in daily_data.items():
                if data_values['y']:
                    x_data.append(day)
                    y_data.append(sum(data_values['y']) / len(data_values['y']))

        if averaging_chart.get() == "Без осреднения":   
            x_data = device_data['Дата'].tolist()
            for index, row in device_data.iterrows():
                if 'data' in row and axis_y.get() in row['data']:
                    y_data.append(float(row['data'][axis_y.get()]))
                
    graph_frame = tk.Tk()
    graph_frame.title("График")

    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)
    if type_chart.get() == "Линейный":
        ax.plot(x_data, y_data, label=f'{axis_y.get()}')
    elif type_chart.get() == "Столбчатый":
        ax.bar(x_data, y_data, label=f'{axis_y.get()}')
    elif type_chart.get() == "Точечный":
        ax.scatter(x_data, y_data, label=f'{axis_y.get()}')

    y_data_additional=[]
    for y_axis in additional_y_axes:
        y_axis_label = y_axis.get()
        if y_axis_label:
            if json_data is not None:
                data = json_data
                data = data[(data['Date'] >= start_datetime) & (data['Date'] <= end_datetime)]
                selected_device = device_combobox.get()
                device_name = selected_device.split(" (")[0]  
                serial_number = selected_device.split(" (")[1].replace(")", "") if " (" in selected_device else "01" 
                device_data = json_data[(json_data['uName'] == device_name) & (json_data['serial'] == serial_number)] 

                device_data.loc[:, 'Дата'] = pd.to_datetime(device_data['Дата'], errors='coerce')

                if averaging_chart.get() == "Осреднить за час":
                    hourly_data = {}  
                    for index, row in device_data.iterrows():
                        timestamp = row['Дата']
                        hour = timestamp.replace(minute=0, second=0, microsecond=0)  
                        if hour not in hourly_data:
                            hourly_data[hour] = {'y': []}
                        
                        if 'data' in row and y_axis.get() in row['data']:
                            hourly_data[hour]['y'].append(float(row['data'][y_axis.get()]))

                    for hour, data_values in hourly_data.items():
                        if data_values['y']:
                            y_data_additional.append(sum(data_values['y']) / len(data_values['y']))

                if averaging_chart.get() == "Осреднить за 3 часа":
                    three_hour_data = {}
                    for index, row in device_data.iterrows():
                        timestamp = row['Дата']
                        three_hour_interval = timestamp.replace(minute=0, second=0, microsecond=0) - timedelta(hours=timestamp.hour % 3)
                        if three_hour_interval not in three_hour_data:
                            three_hour_data[three_hour_interval] = {'y': []}
                        
                        if 'data' in row and y_axis.get() in row['data']:
                            three_hour_data[three_hour_interval]['y'].append(float(row['data'][y_axis.get()]))

                    for interval, data_values in three_hour_data.items():
                        if data_values['y']:
                            y_data_additional.append(sum(data_values['y']) / len(data_values['y']))

                if averaging_chart.get() == "Осреднить за день":
                    daily_data = {}
                    for index, row in device_data.iterrows():
                        timestamp = row['Дата']
                        day = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)  
                        if day not in daily_data:
                            daily_data[day] = {'y': []}
                        
                        if 'data' in row and y_axis.get() in row['data']:
                            daily_data[day]['y'].append(float(row['data'][y_axis.get()]))

                    for day, data_values in daily_data.items():
                        if data_values['y']:
                            y_data_additional.append(sum(data_values['y']) / len(data_values['y']))

                if averaging_chart.get() == "Без осреднения":   
                    for index, row in device_data.iterrows():
                        if 'data' in row and y_axis.get() in row['data']:
                            y_data_additional.append(float(row['data'][y_axis.get()]))
                
            if csv_data is not None:
                y_data_additional = data_resampled[y_axis.get()]
            
            if type_chart.get() == "Линейный":
                ax.plot(x_data, y_data_additional, label=f'{y_axis.get()}')
            elif type_chart.get() == "Столбчатый":
                ax.bar(x_data, y_data_additional, label=f'{y_axis.get()}')
            elif type_chart.get() == "Точечный":
                ax.scatter(x_data, y_data_additional, label=f'{y_axis.get()}')
         

    ax.set_xlabel('Дата')
    ax.set_ylabel('Значение')
    ax.legend()
    ax.grid(True)

    if json_data is not None:
        min_data, max_data = get_min_max(device_data, axis_x.get(), axis_y.get())
    if csv_data is not None:
        min_data, max_data = get_min_max(data_resampled, axis_x.get(), axis_y.get())
    
    if min_data[0] is not None:
        min_date = pd.to_datetime(min_data[0])  
        ax.annotate(f"Минимум: {min_data[1]}\nДата: {min_date.strftime('%Y-%m-%d %H:%M:%S')}", 
                    xy=(min_date, min_data[1]), 
                    xytext=(min_date, min_data[1] + (max(y_data) - min(y_data)) * 0.1),
                    arrowprops=dict(facecolor='red', shrink=0.05))

    if max_data[0] is not None:
        max_date = pd.to_datetime(max_data[0])
        ax.annotate(f"Максимум: {max_data[1]}\nДата: {max_date.strftime('%Y-%m-%d %H:%M:%S')}", 
                    xy=(max_date, max_data[1]), 
                    xytext=(max_date, max_data[1] + (max(y_data) - min(y_data)) * 0.1),
                    arrowprops=dict(facecolor='blue', shrink=0.05))
    for widget in graph_frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, graph_frame)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

y_et=[]
def et(data):
    y_et=[]
    t_data=[]
    h_data=[]
    if csv_data is not None:
        t_data = data['BME280_temp']
        h_data = data['BME280_humidity']
        
    elif json_data is not None:
        selected_device = device_combobox.get()
        device_name = selected_device.split(" (")[0]  
        serial_number = selected_device.split(" (")[1].replace(")", "") if " (" in selected_device else "01" 
        device_data = json_data[(json_data['uName'] == device_name) & (json_data['serial'] == serial_number)] 
        for index, row in device_data.iterrows():
            if 'data' in row and 'BME280_temp' in row['data'] and 'BME280_humidity' in row['data']:
                t_data.append(float(row['data']['BME280_temp']))
                h_data.append(float(row['data']['BME280_humidity']))
    for (t, h) in zip(t_data, h_data):
                y_et.append(t - 0.4 * (t - 10) * (1 - h / 100))

    return y_et
    
def chart_et():
    if csv_data is not None:
        data = csv_data
        start_datetime = data['Дата'].min().strftime('%Y-%m-%d %H:%M:%S')
        end_datetime = data['Дата'].max().strftime('%Y-%m-%d %H:%M:%S')
        data = data[(data['Date'] >= start_datetime) & (data['Date'] <= end_datetime)]
        x_data = data[axis_x.get()]
    elif json_data is not None:
        data = json_data
        start_datetime = data['Дата'].min().strftime('%Y-%m-%d %H:%M:%S')
        end_datetime = data['Дата'].max().strftime('%Y-%m-%d %H:%M:%S')
        data = data[(data['Date'] >= start_datetime) & (data['Date'] <= end_datetime)]
        selected_device = device_combobox.get()
        device_name = selected_device.split(" (")[0]  
        serial_number = selected_device.split(" (")[1].replace(")", "") if " (" in selected_device else "01" 
        device_data = data[(data['uName'] == device_name) & (data['serial'] == serial_number)] 
        x_data = device_data['Дата'].tolist()
    else:
        print("Нет данных для построения графика.")
        return

        y_axis_et=et(data)

    if x_data is not None and y_axis_et is not None:
        graph_frame = tk.Tk()
        graph_frame.title("График")

        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(x_data, y_axis_et)     

        ax.set_xlabel('Дата')
        ax.set_ylabel('Значение')
        ax.grid(True)
        
        for widget in graph_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, graph_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

#Индекс комфорта
def comfort_index(temp):
    if temp > 30:
        return 'Очень жарко'
    elif 24 <= temp <= 30:
        return 'Жарко'
    elif 18 <= temp < 24:
        return 'Тепло'
    elif 12 <= temp < 18:
        return 'Умеренно тепло'
    elif 6 <= temp < 12:
        return 'Прохладно'
    elif 0 <= temp < 6:
        return 'Умеренно'
    elif -12 <= temp < 0:
        return 'Холодно'
    elif -24 <= temp < -12:
        return 'Очень холодно'
    elif temp < -24:
        return 'Крайне холодно'
    return 'Неизвестно'

def chart_comfort():
    x_data=[]
    y_data=[]

    if csv_data is not None:
        data = csv_data
        start_datetime = data['Дата'].min().strftime('%Y-%m-%d %H:%M:%S')
        end_datetime = data['Дата'].max().strftime('%Y-%m-%d %H:%M:%S')
        data = data[(data['Date'] >= start_datetime) & (data['Date'] <= end_datetime)]
        y_data = data['BME280_temp'].apply(comfort_index)
        x_data = data[axis_x.get()]
    elif json_data is not None:
        data = json_data
        start_datetime = data['Дата'].min().strftime('%Y-%m-%d %H:%M:%S')
        end_datetime = data['Дата'].max().strftime('%Y-%m-%d %H:%M:%S')
        data = data[(data['Date'] >= start_datetime) & (data['Date'] <= end_datetime)]
        selected_device = device_combobox.get()
        device_name = selected_device.split(" (")[0]  
        serial_number = selected_device.split(" (")[1].replace(")", "") if " (" in selected_device else "01" 
        device_data = data[(data['uName'] == device_name) & (data['serial'] == serial_number)] 
        x_data = device_data['Дата'].tolist()
        for index, row in device_data.iterrows():
            if 'data' in row and 'BME280_temp' in row['data']:
                temp = float(row['data']['BME280_temp'])
                y_data.append(comfort_index(temp))
    else:
        print("Нет данных для построения графика.")
        return

    if x_data is not None and y_data is not None:
        graph_frame = tk.Tk()
        graph_frame.title("График")

        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(x_data, y_data)     
        ax.set_yticks(['Очень жарко', 'Жарко', 'Тепло', 'Умеренно тепло', 'Прохладно', 'Умеренно', 'Холодно', 'Очень холодно', 'Крайне холодно'])
        ax.set_xlabel('Дата')
        ax.set_ylabel('Значение')
        ax.grid(True)
        
        for widget in graph_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, graph_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    

#Кнопки (гр. интерфейс)
root = tk.Tk()
root.title("Графики")
root.minsize(650, 550)


csv_button = tk.Button(root, text="Выбрать CSV файл", command=select_csv_file)
csv_button.place(x=20, y =5)
csv_file_label = tk.Label(root, text="CSV файл не выбран")
csv_file_label.place(x=20, y=40)

json_button = tk.Button(root, text="Выбрать JSON файл", command=select_json_file)
json_button.place(x=240, y=5)
json_file_label = tk.Label(root, text="JSON файл не выбран")
json_file_label.place(x=240, y=40)

date_range_label = tk.Label(root, text="Диапазон дат не установлен")
date_range_label.place(x=20, y=70)

axis_x = StringVar(value='Дата') 
axis_y = StringVar()
device = StringVar()

x_label = tk.Label(root, text="Добавьте ось X")
x_label.place(x=20, y=100)
x_combobox = ttk.Combobox(root, textvariable=axis_x)
x_combobox.place(x=20, y=130)

y_label = tk.Label(root, text="Добавьте ось Y")
y_label.place(x=240,y=100)
y_combobox = ttk.Combobox(root, textvariable=axis_y)
y_combobox.place(x=240, y=130)

device_combobox = ttk.Combobox(root, textvariable=device)
  
averaging_chart_label = tk.Label(root, text="График:")
averaging_chart_label.place(x=20, y=160)

averaging_chart = tk.StringVar()
non_averaging = tk.Radiobutton(text="Без осреднения", variable=averaging_chart, value="Без осреднения")
non_averaging.place(x=20, y=190)
hour_button = tk.Radiobutton(text="Осреднить за час", variable=averaging_chart, value="Осреднить за час")
hour_button.place(x=20, y=220)
three_hour_button = tk.Radiobutton(root, text="Осреднить за 3 часа", variable=averaging_chart, value="Осреднить за 3 часа")
three_hour_button.place(x=20, y=250)
day_button = tk.Radiobutton(root, text="Осреднить за день", variable=averaging_chart, value="Осреднить за день")
day_button.place(x=20, y=280)

type_chart_label = tk.Label(root, text="Выберите тип графика:")
type_chart_label.place(x=240, y=160)

type_chart = tk.StringVar()

line_button = tk.Radiobutton(text="Линейный", variable=type_chart, value="Линейный")
line_button.place(x=240, y=190)
column_button = tk.Radiobutton(text="Столбчатый", variable=type_chart, value="Столбчатый")
column_button.place(x=240, y=220)
drugoe_button = tk.Radiobutton(text="Точечный", variable=type_chart, value="Точечный")
drugoe_button.place(x=240, y=250)

btn = tk.Button(text="Построить график ЭТ", command=chart_et)
btn.place(x=20, y=310)

btn = tk.Button(text="Построить график теплоощущения", command=chart_comfort)
btn.place(x=240, y=310)

add_y_button = tk.Button(root, text="+ Добавить ось Y", command=add_y_axis)
add_y_button.place(x=240, y=340)

btn = tk.Button(text="Построить график", command=charts)
btn.place(x=20, y=340)

tk.mainloop()
