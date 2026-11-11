param(
    [Parameter(Mandatory = $true)][string]$TextFile,
    [Parameter(Mandatory = $true)][string]$WaveFile,
    [int]$Rate = -1,
    [string]$Culture = "en"
)

# Reads the warning aloud using the voices built into Windows.
# Called from speech.py. Kept as a separate file so no text has to be
# escaped into a command line.

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech

$text = Get-Content -LiteralPath $TextFile -Raw -Encoding UTF8

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    # Picks an installed voice for the language. Hong Kong voices come first for Chinese.
    $voices = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like "$Culture-*" })
    if ($voices.Count -eq 0) {
        throw "No voice for $Culture"
    }
    $preferred = @($voices | Where-Object { $_.VoiceInfo.Culture.Name -eq "zh-HK" })
    if ($preferred.Count -eq 0) {
        $preferred = $voices
    }
    $synth.SelectVoice($preferred[0].VoiceInfo.Name)
    # -1 is slightly slower than normal: elderly listeners need the pause.
    $synth.Rate = $Rate
    $synth.SetOutputToWaveFile($WaveFile)
    $synth.Speak($text)
}
finally {
    $synth.Dispose()
}
