import os
import shutil
import json
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.core.infrastructure.strategy_provider import StrategyProvider
from aide.features.code_refactoring.application.move_file import MoveFileUseCase

def test_move_file_with_xml_references(tmp_path):
    # 1. Setup Mock Project
    project_dir = tmp_path / "mock_project"
    project_dir.mkdir()
    
    src_root = project_dir / "app/src/main/java"
    src_root.mkdir(parents=True)
    
    source_dir = src_root / "com/example/old"
    source_dir.mkdir(parents=True)
    
    dest_dir = src_root / "com/example/new"
    
    # Create MainActivity.kt
    main_activity_path = source_dir / "MainActivity.kt"
    main_activity_content = """package com.example.old

class MainActivity : Activity() {
    override fun onCreate() {
        setContentView(R.layout.activity_main)
    }
}
"""
    main_activity_path.write_text(main_activity_content)
    
    # Create AndroidManifest.xml referencing old package
    manifest_dir = project_dir / "app/src/main"
    manifest_path = manifest_dir / "AndroidManifest.xml"
    manifest_content = """<manifest>
    <application>
        <activity android:name="com.example.old.MainActivity" />
    </application>
</manifest>
"""
    manifest_path.write_text(manifest_content)

    # 2. Execute move-file
    fs = OsFileSystem(str(project_dir))
    strategy_provider = StrategyProvider()
    
    use_case = MoveFileUseCase(fs, strategy_provider)
    
    res = use_case.execute(
        source_paths=[str(main_activity_path)],
        dest_dir=str(dest_dir),
        root_path=str(project_dir),
        src_root="app/src/main/java"
    )
    
    # 3. Assertions
    assert res.success is True
    assert res.files_changed == 1
    assert res.total_replacements > 0 # Should have updated the manifest

    # Check file was moved
    new_activity_path = dest_dir / "MainActivity.kt"
    assert new_activity_path.exists()
    assert not main_activity_path.exists()
    
    # Check package declaration was updated
    new_kt_content = new_activity_path.read_text()
    assert "package com.example.new" in new_kt_content
    assert "package com.example.old" not in new_kt_content
    
    # Check XML reference was updated
    new_manifest_content = manifest_path.read_text()
    assert "com.example.new.MainActivity" in new_manifest_content
    assert "com.example.old.MainActivity" not in new_manifest_content
