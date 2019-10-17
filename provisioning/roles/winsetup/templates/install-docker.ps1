# https://docs.docker.com/install/windows/docker-ee/#use-a-script-to-install-docker-ee

# we could download this in ansible by:
# https://docs.ansible.com/ansible/latest/modules/win_get_url_module.html#win-get-url-module

# it would be possible to get this url by the JSON index:
# https://dockermsft.blob.core.windows.net/dockercontainer/DockerMsftIndex.json

$ErrorActionPreference = "Stop"

Invoke-WebRequest -UseBasicParsing -OutFile "$($env:tmp)\docker.zip" https://download.docker.com/components/engine/windows-server/19.03/docker-19.03.3.zip

# Extract the archive to c:\docker
Expand-Archive "$($env:tmp)\docker.zip" c:\

$installpath = "c:\docker"

# Add Docker to the path for the current session.
$env:path += ";$installpath"

# Optionally, modify PATH to persist across sessions.
$newPath = "$installpath;" +
[Environment]::GetEnvironmentVariable("PATH",
[EnvironmentVariableTarget]::Machine)

[Environment]::SetEnvironmentVariable("PATH", $newPath,
[EnvironmentVariableTarget]::Machine)

# Register the Docker daemon as a service.
dockerd --register-service

# Start the Docker service.
Start-Service docker