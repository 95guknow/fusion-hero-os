Write-Host "=== Konsolidierung ALTE_Frau_95g_Beste_Version ===" | Write-Host

$ErrorActionPreference='SilentlyContinue'
$base = "C:\Users\Admin\Desktop\ALTE_Frau_95g_Beste_Version"
$todo = @(
    @("Rust-Prototyp Quellcode","$base\03_Code\Rust_Prototype\src"),
    @("Hero_Buch_App","$base\04_Buch_und_Archiv\Der_Heroischer_Mensch_2026-06-15\Der_Heroische_Mensch"),
    @("Web_Version","$base\04_Buch_und_Archiv\Der_Heroischer_Mensch_2026-06-15\Web_Version"),
    @("CLI_Version","$base\04_Buch_und_Archiv\Der_Heroischer_Mensch_2026-06-15\CLI_Version"),
    @("Framework Source","$base\06_Master_Archive\00_Framework_Core"),
    @("Execution Reports","$base\06_Master_Archive\01_Reports"),
    @("Architecture Docs","$base\06_Master_Archive\04_Architecture")
)
foreach ($t in $todo) {
    $name=$t[0]; $path=$t[1]
    if (Test-Path $path) {
        $count = (Get-ChildItem $path -Recurse -File).Count
        Write-Host "EXISTS: $name => $path (Dateien: $count)"
    } else {
        Write-Host "MISS : $name => $path"
    }
}
