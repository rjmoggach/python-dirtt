from xml.dom.minidom import getDOMImplementation
import os


def set_element_attrs(element, attrs):
    for attr_name, attr_value in attrs.iteritems():
        element.setAttribute(attr_name, attr_value)

def set_top_element_attrs(top_element):
    attrs = {"name":"Project Tree", "version":"0.1.9b","dirname":"{{project_root}}", \
             "basename":"{{project_path}}", "username":"root", "group":"root",\
             "perms":"02755"}
    set_element_attrs(top_element, attrs)
   

def get_test_nested_dirs(top_level_dirs = 5, nested_dirs = 5, default_dir_attrs = {"username":"root",\
                         "group":"root", "perms" : "02755"}):
    impl = getDOMImplementation()

    newdoc = impl.createDocument(None, "dirtt", None)
    top_element = newdoc.documentElement
    set_top_element_attrs(top_element)
    attrs = default_dir_attrs

    for i in range(0, top_level_dirs):
        top_dir_element = newdoc.createElement("dir")

        attrs["name"] = "%s%d" % ("top_dir", i)
        attrs["basename"] = "%s%d" % ("top_dir", i)

        set_element_attrs(top_dir_element, attrs)

        del attrs["name"]
        del attrs["basename"]

        element = top_dir_element
        for j in range(0, nested_dirs):
           new_element = newdoc.createElement("dir") 

           attrs["name"] = "%s%d" % ("nested_dir", j)
           attrs["basename"] = "%s%d" % ("nested_dir", j)

           set_element_attrs(new_element, attrs)

           del attrs["name"]
           del attrs["basename"]

           element.appendChild(new_element)
           element = new_element
        
        top_element.appendChild(top_dir_element)

    return newdoc.toprettyxml()

def get_test_logging_xml():
    impl = getDOMImplementation()

    newdoc = impl.createDocument(None, "dirtt", None)
    top_element = newdoc.documentElement
    set_top_element_attrs(top_element)

    dir_element = newdoc.createElement("dir")
    set_element_attrs(dir_element, {"name":"dir1", "basename":"dir1", \
                      "username":"root", "group":"root", "perms":"02775"})
    
    file_element = newdoc.createElement("file")
    set_element_attrs(file_element, {"name":"file.txt", "basename":"file.txt", \
                      "username":"root", "group":"root", "perms":"02775"})
 
    link_element = newdoc.createElement("link")
    set_element_attrs(link_element, {"basename":"images","ref":"dir1"})
 
    top_element.appendChild(dir_element)
    top_element.appendChild(file_element)
    top_element.appendChild(link_element)

    return newdoc.toprettyxml()

def get_test_dirname1_xml():
    """
    <?xml version="1.0" encoding="UTF-8"?>
    <dirtt name="Project Tree" version="0.1.9b1" dirname="{{project_root}}" basename="{{project_path}}" username="root" group="root" perms="02755">

        <dir name="d1" dirname="d1/d2/d3/d4" basename="d4" perms="02755" username="root" group="root"/>
        <dir name="d1" dirname="d1/d2" basename="d4" perms="02755" username="root" group="root"/>

    </dirtt>
    """
    impl = getDOMImplementation()

    newdoc = impl.createDocument(None, "dirtt", None)
    top_element = newdoc.documentElement

    set_top_element_attrs(top_element)

    dir_element1 = newdoc.createElement("dir")
    set_element_attrs(dir_element1, {"name":"d1","dirname":os.path.join("d1", "d2", "d3"),\
                      "basename":"d4","username":"root","group":"root", "perms":"02775"}) 
    
    dir_element2 = newdoc.createElement("dir")
    set_element_attrs(dir_element2, {"name":"d2","dirname":os.path.join("d1", "d2"),\
                      "basename":"d4","username":"root","group":"root", "perms":"02775"}) 
    
    top_element.appendChild(dir_element1)
    top_element.appendChild(dir_element2)
 
    return newdoc.toprettyxml()

def get_test_dirname2_xml():
    """
     <?xml version="1.0" encoding="UTF-8"?>
     <dirtt name="Project Tree" version="0.1.9b1" dirname="{{project_root}}/{{project_path}}/root" username="root" group="root" perms="02755">

         <dir name="d1" dirname="d1/d2/d3" basename="d4" perms="02755" username="root" group="root"/>
         <dir name="d2" dirname="d1/d2" basename="d4" perms="02755" username="root" group="root"/>

     </dirtt>
    """
    impl = getDOMImplementation()

    newdoc = impl.createDocument(None, "dirtt", None)
    top_element = newdoc.documentElement

    set_top_element_attrs(top_element)
    top_element.setAttribute("dirname", "{{project_root}}/{{project_path}}/root")
    top_element.removeAttribute("basename")

    dir_element1 = newdoc.createElement("dir")
    set_element_attrs(dir_element1, {"name":"d1","dirname":os.path.join("d1", "d2", "d3"),\
                      "basename":"d4","username":"root","group":"root", "perms":"02775"}) 
    
    dir_element2 = newdoc.createElement("dir")
    set_element_attrs(dir_element2, {"name":"d2","dirname":os.path.join("d1", "d2"),\
                      "basename":"d4","username":"root","group":"root", "perms":"02775"}) 

    top_element.appendChild(dir_element1)
    top_element.appendChild(dir_element2)

    return newdoc.toprettyxml()
     
if __name__ == "__main__":
    print get_test_nested_dirs()
