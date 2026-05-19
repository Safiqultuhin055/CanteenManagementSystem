param(
    [string]$Root,
    [string]$PythonExe,
    [string]$VirtualPath = '/cms'
)
$runIis = Join-Path $Root 'deploy\iis\run_iis.py'
$webConfig = Join-Path $Root 'web.config'
$xml = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="httpPlatformHandler" path="*" verb="*"
           modules="httpPlatformHandler" resourceType="Unspecified" />
    </handlers>
    <httpPlatform
      processPath="$PythonExe"
      arguments="&quot;$runIis&quot;"
      stdoutLogEnabled="true"
      stdoutLogFile=".\logs\iis_stdout"
      startupTimeLimit="120"
      processesPerApplication="1">
      <environmentVariables>
        <environmentVariable name="DJANGO_SETTINGS_MODULE" value="canteen_system.settings" />
        <environmentVariable name="PYTHONPATH" value="$Root" />
        <environmentVariable name="PYTHONUNBUFFERED" value="1" />
        <environmentVariable name="FORCE_SCRIPT_NAME" value="$VirtualPath" />
      </environmentVariables>
    </httpPlatform>
    <security>
      <requestFiltering allowDoubleEscaping="true" />
    </security>
  </system.webServer>
</configuration>
"@
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($webConfig, $xml, $utf8)
