from kblab import Archive
import getpass

def main():
    username = input("Username: ")
    password = getpass.getpass()
    print("Password set for user:", username)
    
    a = Archive('https://betalab.kb.se', auth=(username, password))
    
    package_ids = a.search({ 'tags': 'protokoll', 'meta.created': '1985'}, max=200)
    
    print(type(package_ids))
    print("Found", len(package_ids), "matches.")
    
    for package_id in package_ids:
        print("Id:", package_id)
        
        package = a.get(package_id)
        filelist = package.list()
        
        jp2list = [f for f in filelist if f.split(".")[-1] == "jp2"]
        print(jp2list, len(jp2list))
    
if __name__ == "__main__":
    main()

