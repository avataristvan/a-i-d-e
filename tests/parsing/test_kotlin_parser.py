import pytest
from aide.parsing.infrastructure.kotlin_parser import KotlinLanguageParser


def test_kotlin_ast_parsing():
    parser = KotlinLanguageParser()
    content = """
package com.example

class MyService : BaseService() {
    fun doSomething() {}
    fun anotherMethod(): String = "hello"
}

interface IService {
    fun doSomething()
}

object Singleton {
    fun instance() = this
}

data class User(val name: String, val age: Int)

enum class Status { ACTIVE, INACTIVE }

fun topLevelFun() {}
"""

    nodes = parser.parse(content, ".kt")

    class_node = next((n for n in nodes if n.name == "MyService"), None)
    assert class_node is not None
    assert class_node.kind == "class"
    assert len(class_node.children) == 2
    assert class_node.children[0].name == "doSomething"
    assert class_node.children[0].kind == "function"

    interface_node = next((n for n in nodes if n.name == "IService"), None)
    assert interface_node is not None
    assert interface_node.kind == "interface"

    object_node = next((n for n in nodes if n.name == "Singleton"), None)
    assert object_node is not None
    assert object_node.kind == "object"
    assert object_node.children[0].name == "instance"

    data_class = next((n for n in nodes if n.name == "User"), None)
    assert data_class is not None
    assert data_class.kind == "class"

    enum_node = next((n for n in nodes if n.name == "Status"), None)
    assert enum_node is not None
    assert enum_node.kind == "enum"

    top_fn = next((n for n in nodes if n.name == "topLevelFun"), None)
    assert top_fn is not None
    assert top_fn.kind == "function"


def test_kotlin_companion_object():
    parser = KotlinLanguageParser()
    content = """
class MyClass {
    fun method() {}
    companion object {
        fun create() = MyClass()
    }
}
"""
    nodes = parser.parse(content, ".kt")
    class_node = next((n for n in nodes if n.name == "MyClass"), None)
    assert class_node is not None
    companion = next((c for c in class_node.children if c.name == "Companion"), None)
    assert companion is not None
    assert companion.kind == "object"


def test_kotlin_import_parsing():
    parser = KotlinLanguageParser()
    content = """
package com.example

import android.os.Bundle
import com.example.domain.User
import kotlinx.coroutines.flow.Flow

class Foo
"""
    imports = parser.parse_imports(content, ".kt")
    assert len(imports) == 3
    assert "android.os.Bundle" in imports
    assert "com.example.domain.User" in imports
    assert "kotlinx.coroutines.flow.Flow" in imports
