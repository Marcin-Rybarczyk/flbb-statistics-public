$ROOT = $PSScriptRoot
$GAME_SCHEDULE_RAW_DIRECTORY = "C:\temp\test-multiple-file-download"
Add-Type -Path "$ROOT\Net40\HtmlAgilityPack.dll"

$getHtmlContent = {
    param($url, $fileNumber)
    # Define the URL
    $GAME_SCHEDULE_RAW_DIRECTORY = "C:\temp\test-multiple-file-download"
    # Use Invoke-WebRequest to get the HTML content
    $response = Invoke-WebRequest -Uri $url

    # Check if the request was successful (status code 200)
    if ($response.StatusCode -eq 200) {
        # Display the HTML content
        $htmlContent = $response.Content
        Set-Content -Path "$GAME_SCHEDULE_RAW_DIRECTORY\test-$fileNumber.html" -Value $htmlContent
        Write-Host "File saved to $GAME_SCHEDULE_RAW_DIRECTORY\test-$fileNumber.html"
        #         return $htmlContent
    }
    else {
        Write-Error "Failed to retrieve HTML content. Status code: $($response.StatusCode)"
    }
}

function Main {
    # Define the URLs
    $urls = @(
        'https://www.luxembourg.basketball/match/16053/2023-11-19/racing-d/bbc-nitia-b/division2-hommes', 
        'https://www.luxembourg.basketball/match/16051/2023-11-19/racing-c/schieren-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16057/2023-11-19/sparta-c/bc-mess-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16041/2023-11-12/grengewald-hostert-c/racing-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16047/2023-11-12/bbc-nitia-b/contern-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16053/2023-11-19/racing-d/bbc-nitia-b/division2-hommes', 
        'https://www.luxembourg.basketball/match/16051/2023-11-19/racing-c/schieren-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16057/2023-11-19/sparta-c/bc-mess-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16041/2023-11-12/grengewald-hostert-c/racing-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16047/2023-11-12/bbc-nitia-b/contern-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16053/2023-11-19/racing-d/bbc-nitia-b/division2-hommes', 
        'https://www.luxembourg.basketball/match/16051/2023-11-19/racing-c/schieren-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16057/2023-11-19/sparta-c/bc-mess-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16041/2023-11-12/grengewald-hostert-c/racing-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16047/2023-11-12/bbc-nitia-b/contern-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16053/2023-11-19/racing-d/bbc-nitia-b/division2-hommes', 
        'https://www.luxembourg.basketball/match/16051/2023-11-19/racing-c/schieren-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16057/2023-11-19/sparta-c/bc-mess-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16041/2023-11-12/grengewald-hostert-c/racing-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16047/2023-11-12/bbc-nitia-b/contern-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16053/2023-11-19/racing-d/bbc-nitia-b/division2-hommes', 
        'https://www.luxembourg.basketball/match/16051/2023-11-19/racing-c/schieren-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16057/2023-11-19/sparta-c/bc-mess-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16041/2023-11-12/grengewald-hostert-c/racing-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16047/2023-11-12/bbc-nitia-b/contern-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16053/2023-11-19/racing-d/bbc-nitia-b/division2-hommes', 
        'https://www.luxembourg.basketball/match/16051/2023-11-19/racing-c/schieren-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16057/2023-11-19/sparta-c/bc-mess-b/division2-hommes',
        'https://www.luxembourg.basketball/match/16041/2023-11-12/grengewald-hostert-c/racing-c/division2-hommes',
        'https://www.luxembourg.basketball/match/16047/2023-11-12/bbc-nitia-b/contern-c/division2-hommes')

    if (-not (Test-Path "$GAME_SCHEDULE_RAW_DIRECTORY")) {
        New-Item -ItemType Directory -Path "$GAME_SCHEDULE_RAW_DIRECTORY"
    }
    # Run the function for each URL
    $i = 0
    foreach ($url in $urls) {
        $i++
        Start-Job -ScriptBlock $getHtmlContent -ArgumentList $url, $i

    }

    # Wait for all jobs to complete
    while (Get-Job -State "Running") {
        Start-Sleep 1
    }

    # Get the results of the jobs
    $results = Get-Job | Receive-Job

    # Display the results
    $results

    # Clean up the jobs
    Remove-Job -State Completed
}

Main
