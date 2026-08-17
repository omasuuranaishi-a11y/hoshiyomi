param(
    [string]$Destination = "backend/assets/tarot",
    [string[]]$OnlyNumbers = @(),
    [int]$MaximumAttempts = 6
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$destinationRoot = Join-Path $repositoryRoot $Destination
New-Item -ItemType Directory -Force -Path $destinationRoot | Out-Null

$cards = [ordered]@{
    "00" = "Fool"
    "01" = "Magician"
    "02" = "High Priestess"
    "03" = "Empress"
    "04" = "Emperor"
    "05" = "Hierophant"
    "06" = "Lovers"
    "07" = "Chariot"
    "08" = "Strength"
    "09" = "Hermit"
    "10" = "Wheel of Fortune"
    "11" = "Justice"
    "12" = "Hanged Man"
    "13" = "Death"
    "14" = "Temperance"
    "15" = "Devil"
    "16" = "Tower"
    "17" = "Star"
    "18" = "Moon"
    "19" = "Sun"
    "20" = "Judgement"
    "21" = "World"
}

$headers = @{
    "User-Agent" = "omasu-horoscope/1.0 (GitHub: omasuuranaishi-a11y/hoshiyomi)"
}

foreach ($entry in $cards.GetEnumerator()) {
    $number = $entry.Key
    $englishName = $entry.Value
    if ($OnlyNumbers.Count -gt 0 -and $OnlyNumbers -notcontains $number) {
        continue
    }
    $target = Join-Path $destinationRoot "major-$number-rws1909-v1.jpeg"
    if ((Test-Path -LiteralPath $target) -and (Get-Item -LiteralPath $target).Length -ge 100000) {
        Write-Output "present $number $englishName"
        continue
    }

    $sourceName = "${number}_$($englishName -replace ' ', '_').jpg"
    # This public mirror records Wikimedia Commons as its source and the deck
    # as Public Domain. Raw GitHub URLs avoid disrupting Commons with 22
    # sequential image requests during setup.
    $source = "https://raw.githubusercontent.com/mixvlad/TarotCards/main/tarot/rider-waite/720px/$sourceName"
    $temporary = "$target.download"
    $downloaded = $false
    for ($attempt = 1; $attempt -le $MaximumAttempts; $attempt++) {
        try {
            Invoke-WebRequest -Uri $source -Headers $headers -MaximumRedirection 10 -OutFile $temporary
            $downloaded = $true
            break
        }
        catch {
            if (Test-Path -LiteralPath $temporary) {
                Remove-Item -LiteralPath $temporary -Force
            }
            if ($attempt -eq $MaximumAttempts) {
                throw
            }
            $delaySeconds = [Math]::Min(45, [Math]::Pow(2, $attempt + 1))
            Write-Output "retry $attempt/$MaximumAttempts $number $englishName after ${delaySeconds}s"
            Start-Sleep -Seconds $delaySeconds
        }
    }
    if (-not $downloaded) {
        throw "Could not download tarot asset: $sourceName"
    }
    if ((Get-Item -LiteralPath $temporary).Length -lt 100000) {
        throw "Downloaded tarot asset is unexpectedly small: $sourceName"
    }
    Move-Item -LiteralPath $temporary -Destination $target -Force
    Write-Output "downloaded $number $englishName"
    Start-Sleep -Seconds 2
}
