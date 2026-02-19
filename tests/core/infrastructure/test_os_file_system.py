import os
from aide.core.infrastructure.os_file_system import OsFileSystem

def test_write_and_read_file(temp_dir):
    fs = OsFileSystem()
    test_file = os.path.join(temp_dir, "test.txt")
    content = "Hello, AIDE!"
    
    fs.write_file(test_file, content)
    assert os.path.exists(test_file)
    
    read_content = fs.read_file(test_file)
    assert read_content == content

def test_walk_files(temp_dir):
    fs = OsFileSystem()
    os.makedirs(os.path.join(temp_dir, "src"))
    file1 = os.path.join(temp_dir, "src", "file1.txt")
    file2 = os.path.join(temp_dir, "file2.txt")
    os.makedirs(os.path.join(temp_dir, "node_modules"))
    ignored_file = os.path.join(temp_dir, "node_modules", "ignore.txt")
    
    fs.write_file(file1, "1")
    fs.write_file(file2, "2")
    fs.write_file(ignored_file, "ignore")
    
    files = list(fs.walk_files(temp_dir))
    assert len(files) == 2
    assert file1 in files
    assert file2 in files
    assert ignored_file not in files

def test_move_path(temp_dir):
    fs = OsFileSystem()
    src = os.path.join(temp_dir, "src.txt")
    dst = os.path.join(temp_dir, "dst", "dst.txt")
    
    fs.write_file(src, "move_me")
    fs.move_path(src, dst)
    
    assert not os.path.exists(src)
    assert os.path.exists(dst)
    assert fs.read_file(dst) == "move_me"

def test_delete_path(temp_dir):
    fs = OsFileSystem()
    file_path = os.path.join(temp_dir, "delete.txt")
    dir_path = os.path.join(temp_dir, "delete_dir")
    
    fs.write_file(file_path, "del")
    os.makedirs(dir_path)
    
    fs.delete_path(file_path)
    assert not os.path.exists(file_path)
    
    fs.delete_path(dir_path)
    assert not os.path.exists(dir_path)
