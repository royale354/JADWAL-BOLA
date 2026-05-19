$ErrorActionPreference = "Stop"
$Port = 8788
$Root = $PSScriptRoot
$GoalUrl = "https://www.goal.com/id/berita/jadwal-tv-siaran-langsung-sepakbola-hari-ini/1qomojcjyge9n1nr2voxutdc1n"

Add-Type -AssemblyName System.Web

# Muat database logo statis (cepat, tanpa API eksternal)
$LogosFile = Join-Path $Root "logos.json"
$StaticTeams = @{}
$StaticLeagues = @{}
if (Test-Path $LogosFile) {
    $logoData = Get-Content $LogosFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $logoData.teams.PSObject.Properties | ForEach-Object { $StaticTeams[$_.Name] = $_.Value }
    $logoData.leagues.PSObject.Properties | ForEach-Object { $StaticLeagues[$_.Name] = $_.Value }
    Write-Host "  Logo database: $($StaticTeams.Count) klub, $($StaticLeagues.Count) liga" -ForegroundColor DarkGray
}

$script:ApiCache = @{}

$TeamAliases = @{
    "RD Kongo" = "RD Kongo"
    "Brighton & Hove Albion" = "Brighton & Hove Albion"
    "Koln" = "Koln"
    "Hellas Verona" = "Hellas Verona"
    "Al-Hilal" = "Al-Hilal"
    "Al-Nassr" = "Al-Nassr"
    "Arema FC" = "Arema FC"
    "Borneo FC Samarinda" = "Borneo FC Samarinda"
    "Dewa United Banten" = "Dewa United Banten"
    "Bhayangkara Presisi Lampung" = "Bhayangkara Presisi Lampung"
}

function Normalize-Name([string]$Name) {
    return ($Name.ToLower().Trim() -replace '\s+', ' ')
}

function Find-StaticTeamBadge([string]$Name) {
    if ($StaticTeams.ContainsKey($Name)) { return $StaticTeams[$Name] }

    if ($TeamAliases.ContainsKey($Name)) {
        $resolved = $TeamAliases[$Name]
        if ($StaticTeams.ContainsKey($resolved)) { return $StaticTeams[$resolved] }
    }

    $norm = Normalize-Name $Name
    $best = $null
    $bestLen = 0
    foreach ($key in $StaticTeams.Keys) {
        $kNorm = Normalize-Name $key
        if ($norm -eq $kNorm) { return $StaticTeams[$key] }
        if ($norm -like "*$kNorm*" -or $kNorm -like "*$norm*") {
            if ($key.Length -gt $bestLen) {
                $best = $StaticTeams[$key]
                $bestLen = $key.Length
            }
        }
    }
    return $best
}

function Find-StaticLeagueBadge([string]$Name) {
    if ($StaticLeagues.ContainsKey($Name)) { return $StaticLeagues[$Name] }
    $norm = Normalize-Name $Name
    foreach ($key in $StaticLeagues.Keys) {
        $kNorm = Normalize-Name $key
        if ($norm -like "*$kNorm*" -or $kNorm -like "*$norm*") { return $StaticLeagues[$key] }
    }
    return $null
}

function Get-TeamLogoJson([string]$Name) {
    $cacheKey = "team:$Name"
    if ($script:ApiCache.ContainsKey($cacheKey)) { return $script:ApiCache[$cacheKey] }

    $badge = Find-StaticTeamBadge $Name
    $result = (@{ badge = $badge; name = $Name } | ConvertTo-Json -Compress)
    $script:ApiCache[$cacheKey] = $result
    return $result
}

function Get-LeagueLogoJson([string]$Name) {
    $cacheKey = "league:$Name"
    if ($script:ApiCache.ContainsKey($cacheKey)) { return $script:ApiCache[$cacheKey] }

    $badge = Find-StaticLeagueBadge $Name
    $result = (@{ badge = $badge; name = $Name } | ConvertTo-Json -Compress)
    $script:ApiCache[$cacheKey] = $result
    return $result
}

function Get-BatchLogosJson([string[]]$Teams, [string[]]$Leagues) {
    $teamResult = @{}
    $leagueResult = @{}
    foreach ($t in ($Teams | Select-Object -Unique)) {
        if (-not $t) { continue }
        $json = Get-TeamLogoJson $t | ConvertFrom-Json
        $teamResult[$t] = $json.badge
    }
    foreach ($l in ($Leagues | Select-Object -Unique)) {
        if (-not $l) { continue }
        $json = Get-LeagueLogoJson $l | ConvertFrom-Json
        $leagueResult[$l] = $json.badge
    }
    return (@{ teams = $teamResult; leagues = $leagueResult } | ConvertTo-Json -Compress -Depth 4)
}

function Get-ContentType([string]$Path) {
    switch -Regex ([IO.Path]::GetExtension($Path).ToLower()) {
        "\.html?" { "text/html; charset=utf-8" }
        "\.css"   { "text/css; charset=utf-8" }
        "\.js"    { "application/javascript; charset=utf-8" }
        "\.png"   { "image/png" }
        "\.jpg"   { "image/jpeg" }
        "\.jpeg"  { "image/jpeg" }
        "\.webp"  { "image/webp" }
        "\.json"  { "application/json; charset=utf-8" }
        default   { "application/octet-stream" }
    }
}

function Send-Response([System.Net.HttpListenerResponse]$Response, [int]$Code, [byte[]]$Bytes, [string]$ContentType) {
    $Response.StatusCode = $Code
    $Response.ContentType = $ContentType
    $Response.ContentLength64 = $Bytes.Length
    $Response.OutputStream.Write($Bytes, 0, $Bytes.Length)
    $Response.OutputStream.Close()
}

function Send-Text([System.Net.HttpListenerResponse]$Response, [int]$Code, [string]$Body, [string]$ContentType) {
    Send-Response $Response $Code ([Text.Encoding]::UTF8.GetBytes($Body)) $ContentType
}

function Send-File([System.Net.HttpListenerResponse]$Response, [string]$FilePath) {
    if (-not (Test-Path $FilePath)) {
        Send-Text $Response 404 "Not Found" "text/plain"
        return
    }
    $Response.Headers.Add("Access-Control-Allow-Origin", "*")
    $bytes = [IO.File]::ReadAllBytes($FilePath)
    Send-Response $Response 200 $bytes (Get-ContentType $FilePath)
}

function Fetch-GoalSchedule {
    $headers = @{
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "Accept-Language" = "id-ID,id;q=0.9"
    }
    return Invoke-WebRequest -Uri $GoalUrl -Headers $headers -UseBasicParsing -TimeoutSec 30
}

function Resolve-TeamQuery([string]$Name) { return $Name }

function Proxy-Image([string]$ImageUrl) {
    $allowed = @("football-data.org", "flagcdn.com", "wikimedia.org", "wikipedia.org", "thesportsdb.com", "website-files.com", "cdnlogo.com", "logotyp.us")
    $ok = $false
    foreach ($host in $allowed) {
        if ($ImageUrl -like "*$host*") { $ok = $true; break }
    }
    if (-not $ok) { throw "Host not allowed" }
    $headers = @{ "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" }
    return Invoke-WebRequest -Uri $ImageUrl -Headers $headers -UseBasicParsing -TimeoutSec 20
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()

Write-Host ""
Write-Host "  Jadwal Bola - Server lokal aktif" -ForegroundColor Green
Write-Host "  Buka: http://localhost:$Port" -ForegroundColor Cyan
Write-Host "  Tekan Ctrl+C untuk berhenti" -ForegroundColor DarkGray
Write-Host ""

Start-Process "http://localhost:$Port"

function Handle-Request($Context) {
    $request = $Context.Request
    $response = $Context.Response
    $path = $request.Url.LocalPath

    try {
        if ($path -eq "/api/jadwal") {
            $result = Fetch-GoalSchedule
            Send-Text $response 200 $result.Content "text/html; charset=utf-8"
            return
        }

        if ($path -eq "/api/logo/team") {
            $name = $request.QueryString["name"]
            if (-not $name) {
                Send-Text $response 400 '{"error":"name required"}' "application/json"
                return
            }
            Send-Text $response 200 (Get-TeamLogoJson $name) "application/json; charset=utf-8"
            return
        }

        if ($path -eq "/api/logo/league") {
            $name = $request.QueryString["name"]
            if (-not $name) {
                Send-Text $response 400 '{"error":"name required"}' "application/json"
                return
            }
            Send-Text $response 200 (Get-LeagueLogoJson $name) "application/json; charset=utf-8"
            return
        }

        if ($path -eq "/api/logos/batch") {
            $teamsRaw = $request.QueryString["teams"]
            $leaguesRaw = $request.QueryString["leagues"]
            $teams = @()
            $leagues = @()
            if ($teamsRaw) { $teams = $teamsRaw -split '\|' }
            if ($leaguesRaw) { $leagues = $leaguesRaw -split '\|' }
            Send-Text $response 200 (Get-BatchLogosJson $teams $leagues) "application/json; charset=utf-8"
            return
        }

        if ($path -eq "/api/img") {
            $imgUrl = $request.QueryString["url"]
            if (-not $imgUrl -or -not $imgUrl.StartsWith("https://")) {
                Send-Text $response 400 "Invalid url" "text/plain"
                return
            }
            $img = Proxy-Image $imgUrl
            $ct = if ($img.Headers["Content-Type"]) { $img.Headers["Content-Type"] } else { "image/png" }
            Send-Response $response 200 $img.Content $ct
            return
        }

        if ($path -eq "/" -or $path -eq "") {
            Send-File $response (Join-Path $Root "index.html")
            return
        }

        $safePath = $path.TrimStart("/") -replace "\.\.", ""
        $filePath = Join-Path $Root $safePath
        Send-File $response $filePath
    }
    catch {
        Send-Text $response 500 ("Error: " + $_.Exception.Message) "text/plain; charset=utf-8"
    }
}

try {
    while ($listener.IsListening) {
        $ctx = $listener.GetContext()
        [System.Threading.ThreadPool]::QueueUserWorkItem(
            [System.Threading.WaitCallback]{ param($state) Handle-Request $state },
            $ctx
        )
    }
}
finally {
    $listener.Stop()
}
