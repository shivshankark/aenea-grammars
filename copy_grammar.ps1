param (
[string]$grammar
)
$ErrorActionPreference = "Stop"
IF ($grammar.Equals("")) {
    echo "Usage: %~df0 <grammar_foldername>"
    echo "e.g. %~df0 _vim"
    Exit
}
echo "Copying $grammar"

IF ($grammar.Equals("vocabulary_config")) {
    robocopy e:\aenea-grammars\$grammar\ $Env:AENEA_ROOT\$grammar\ "/S"
} ELSE {
    robocopy e:\aenea-grammars\$grammar\ $Env:AENEA_ROOT\ "*.py"
    robocopy e:\aenea-grammars\$grammar\ $Env:AENEA_ROOT\grammar_config\ "*.example" "/S"
    Set-Location -Path $Env:AENEA_ROOT\grammar_config\
    Dir *.example | move-item -destination { $_.name -replace '\.example$','' } -force
}

echo "Stopping dragon"
taskkill /IM natspeak.exe /F

timeout 1

echo "Starting dragon"
start-process -filepath "C:\Program Files (x86)\Nuance\NaturallySpeaking13\Program\natspeak.exe"
Set-Location -Path e:\aenea-grammars\
