echo "Stopping dragon"
taskkill /IM natspeak.exe /F

timeout 1

echo "Starting dragon"
start-process -filepath "C:\Program Files (x86)\Nuance\NaturallySpeaking13\Program\natspeak.exe"
Set-Location -Path e:\aenea-grammars\tools\