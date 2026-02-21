import os
from aide.core.infrastructure.os_file_system import OsFileSystem

def test_os_file_system_transaction_rollback_write(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    file_path = os.path.join(temp_dir, "test.txt")
    
    # Initial state
    fs.write_file(file_path, "initial content")
    
    # Transaction
    fs.start_transaction()
    fs.write_file(file_path, "modified content")
    assert fs.read_file(file_path) == "modified content"
    
    # Rollback
    fs.rollback()
    
    # Verify rollback
    assert fs.read_file(file_path) == "initial content"

def test_os_file_system_transaction_rollback_create_new(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    file_path = os.path.join(temp_dir, "new_folder", "new_test.txt")
    
    fs.start_transaction()
    fs.write_file(file_path, "new content")
    assert os.path.exists(file_path)
    
    fs.rollback()
    
    assert not os.path.exists(file_path)
    # The new_folder should also be cleaned up since it was created during the transaction
    assert not os.path.exists(os.path.join(temp_dir, "new_folder"))

def test_os_file_system_transaction_rollback_delete(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    file_path = os.path.join(temp_dir, "to_delete.txt")
    
    fs.write_file(file_path, "content to delete")
    
    fs.start_transaction()
    fs.delete_path(file_path)
    assert not os.path.exists(file_path)
    
    fs.rollback()
    
    assert os.path.exists(file_path)
    assert fs.read_file(file_path) == "content to delete"

def test_os_file_system_transaction_rollback_move(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    src_path = os.path.join(temp_dir, "src.txt")
    dst_path = os.path.join(temp_dir, "dst.txt")
    
    fs.write_file(src_path, "move me")
    
    fs.start_transaction()
    fs.move_path(src_path, dst_path)
    assert not os.path.exists(src_path)
    assert os.path.exists(dst_path)
    
    fs.rollback()
    
    assert os.path.exists(src_path)
    assert not os.path.exists(dst_path)
    assert fs.read_file(src_path) == "move me"

def test_os_file_system_transaction_commit(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    file_path = os.path.join(temp_dir, "test.txt")
    
    fs.write_file(file_path, "initial content")
    
    fs.start_transaction()
    fs.write_file(file_path, "modified content")
    fs.commit()
    
    # Rollback after commit should do nothing
    fs.rollback()
    
    assert fs.read_file(file_path) == "modified content"
