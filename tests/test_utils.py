from xml.dom.minidom import getDOMImplementation

"""
<dirtt name="Project Tree" version="0.1.9b1" dirname="{{project_root}}" basename="{{project_path}}" username="root" group="root" perms="02755">

  <dir name="dir1" basename="dir1" username="root" group="root" perms="02775"/>
    <file basename="file.txt" username="root" group="root" perms="02775"/>
      <link basename="images" ref="dir1"/>

      </dirtt>
"""
def get_test_logging_xml():
    impl = getDOMImplementation()

    newdoc = impl.createDocument(None, "dirtt", None)
    top_element = newdoc.documentElement
    top_element.setAttribute("name", "Project Tree")
    top_element.setAttribute("version", "0.1.9b1")
    top_element.setAttribute("dirname", "{{project_root}}")
    top_element.setAttribute("basename", "{{project_path}}")
    top_element.setAttribute("username", "root")
    top_element.setAttribute("group", "root")
    top_element.setAttribute("perms", "02755")

    dir_element = newdoc.createElement("dir")
    dir_element.setAttribute("name","dir1")
    dir_element.setAttribute("basename", "dir1")
    dir_element.setAttribute("username", "root")
    dir_element.setAttribute("group", "root")
    dir_element.setAttribute("perms", "02775")
    
    file_element = newdoc.createElement("file")
    file_element.setAttribute("basename", "file.txt")
    file_element.setAttribute("username", "root")
    file_element.setAttribute("group", "root")
    file_element.setAttribute("perms", "02775")

    link_element = newdoc.createElement("link")
    link_element.setAttribute("basename", "images")
    link_element.setAttribute("ref", "dir1")

    top_element.appendChild(dir_element)
    top_element.appendChild(file_element)
    top_element.appendChild(link_element)

    return newdoc.toxml()
