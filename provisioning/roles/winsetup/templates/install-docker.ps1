# https://docs.docker.com/install/windows/docker-ee/#use-a-script-to-install-docker-ee

# we could download this in ansible by:
# https://docs.ansible.com/ansible/latest/modules/win_get_url_module.html#win-get-url-module

# it would be possible to get this url by the JSON index:
# https://dockermsft.blob.core.windows.net/dockercontainer/DockerMsftIndex.json

$ErrorActionPreference = "Stop"
$zipPath = "c:\docker.zip"
$installpath = "c:\docker"

if(Test-Path $installpath) {
    Write-Host "$installpath exists, docker is installed. (ANSIBLE_OK)"
    exit 0
}

##############################################
# Download raw docker zip package 
#
# this is done in the script. https://github.com/ansible/ansible/issues/637354
# If my issue is resolved, we may move this to tasks/main.yml again

# try to expand first, so a partial download can be checked
$url = "{{docker_download_url}}"

try {
    Expand-Archive "c:\docker.zip" "c:\"
} catch {
    Write-Host "Need to download docker.zip from $url"
    Invoke-WebRequest -UseBasicParsing -OutFile $zipPath $url
}

# Add Docker to the path for the current session.
$env:path += ";$installpath"

# Optionally, modify PATH to persist across sessions.
$newPath = "$installpath;" +
[Environment]::GetEnvironmentVariable("PATH",
[EnvironmentVariableTarget]::Machine)

[Environment]::SetEnvironmentVariable("PATH", $newPath,
[EnvironmentVariableTarget]::Machine)

# Register the Docker daemon as a service.
cd $installpath
dockerd --register-service

exit 0
