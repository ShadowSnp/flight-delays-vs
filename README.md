# Flight Delay Analyzer — Visual Studio Edition

A Python desktop app for analyzing flight delays.  
**Design:** clean light / Microsoft Fluent theme (white + blue).

## How to run

```bash
pip install -r requirements.txt
python app.py
```

Or in **Visual Studio** / **VS Code**: open the folder, set the Python interpreter, then press **Run**.

## Features

| Feature | Details |
|---|---|
| Upload box | Drag & drop **or** browse — CSV / Excel |
| First 10 rows | Striped table shown instantly after upload |
| Task 3 | Bar chart — delay by cause |
| Task 4 | Histogram — ArrDelay distribution |
| Task 5 | Scatter — flight volume vs delay |
| Task 6 | Line — delay trend (auto-groups by year / month / carrier) |
| Task 7 | Statistics panel — top cause, worst period, correlation |
| Task 8 | Saves 4-panel summary PNG → `output/` |

## Dataset columns used

`month` · `carrier_name` · `airport` · `arr_flights` · `arr_delay`  
`carrier_delay` · `weather_delay` · `nas_delay` · `security_delay` · `late_aircraft_delay` · `arr_cancelled`
