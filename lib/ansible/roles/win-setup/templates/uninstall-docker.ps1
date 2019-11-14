# https://docs.docker.com/install/windows/docker-ee/#use-a-script-to-install-docker-ee

# we could download this in ansible by:
# https://docs.ansible.com/ansible/latest/modules/win_get_url_module.html#win-get-url-module

# it would be possible to get this url by the JSON index:
# https://dockermsft.blob.core.windows.net/dockercontainer/DockerMsftIndex.json

$ErrorActionPreference = "Stop"
$installpath = "c:\docker"

if(!Test-Path $installpath) {
    Write-Host "$installpath doen't exist. Exiting."
    exit 0
}

if(Get-Service "docker") {
    Write-Host "Unregister Docker service"
    # Unregister the Docker daemon as a service.
    cd $installpath
    dockerd --unregister-service
    cd \
}

function getpath ($path) {
    return ($path.Split(';') | Where-Object { $_ -ne $installpath }) -join ';'
}

# delete c:\docker
Write-Host "Delete $installpath"
Remove-Item -LiteralPath $installpath -Force -Recurse

# remove c:\docker from the PATH for the current session.
Write-Host "Update $env:path"
$env:path = getpath($env:path)

# remove c:\docker from global PATH.
Write-Host "Update machine-level PATH"
[Environment]::SetEnvironmentVariable(
    "PATH", getpath([Environment]::GetEnvironmentVariable("PATH", [EnvironmentVariableTarget]::Machine)),
    [EnvironmentVariableTarget]::Machine
)


exit 0
