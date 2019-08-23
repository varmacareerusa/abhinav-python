from jenkinsapi import Jenkins 
import sys
import xml.etree.ElementTree as ET
from pexpect import pxssh
import jenkins 
import os

def check():
   print("./plugin1.py <GoldCopyMaster_URL> <GoldCopyMaster_Username> <GoldCopyMaster_Password> <RemoteJenkins_URL> <RemoteJenkins_Username> <RemoteJenkins_Password> <Remote_Host> <Remote_User> <Remote_Password>" )
   sys.exit(0)    


def save_goldcopy_info(url,username,password):
   GoldCopy=Jenkins(url,username,password)
   data1= GoldCopy.plugins._data

   # Created a csv file to store plugin name and version
   fg = open("plugin.csv","w")
   fg.write("Plugin Name,Version\n\n")

   for i in data1['plugins']:
       fg.write(i['shortName']+","+i['version'] )
       fg.write('\n')
   fg.close()   


def match_plugins(url,username,password):
   RemoteInstance=Jenkins(url,username,password) 
   data2= RemoteInstance.plugins._data

   # Reading Gold Copy Instance Plugins Information from plugin.csv file and map to other instance
   f1 = open("plugin.csv","r")
   f = f1.readlines()
   
   # Generating Report to report.csv file 
   f2 = open("report.csv","w") 
   
   # Here f[2:] implies to read file from line 3 of plugin.csv file. So that it ignores reading titles[Plugin Name,Version]
   print("Total Plugins in Gold Copy Jenkins Instance -- "+str(len(f[2:]))) 
   print("-----------------------------------------------------------------")
   print("Total Plugins in Remote Jenkins Instance -- "+str(len(data2['plugins'])))
   print("-----------------------------------------------------------------")
   
   count = 0            # To get total number of matched plugins
   count2 = 0           # To get total number of unmatched plugins due to version
   count3 = 0           # To get total number of unavailable plugins

   f2.write("------Plugin Matched-------\n")
   f2.write("Plugin Name,Version"+"\n\n")
      
   # Loop for matching the plugins along with version
   for i in f[2:]:    
       for j in data2['plugins']:
           if (i.split(",")[0] == j['shortName'] and i.split(",")[1].strip() == j['version']):
               print ("Plugin Matched --- "+ i.split(",")[0]+"  "+i.split(",")[1].strip())
              
               f2.write(i.split(",")[0]+","+i.split(",")[1].strip()+'\n')
               count+=1
   print("-----------------------------------------------------------------")
   print("Total Plugins Matched with version is  -- "+ str(count))
   print("-----------------------------------------------------------------")
   
   f2.write("\n------Plugin UnMatched due to version-------\n")
   f2.write("Plugin Name,Gold Copy Jenkins Instance Version,Remote Jenkins Instance Version"+"\n\n")
   # Loop for Unmatched plugins due to version
   for i in f[2:]:    
       for j in data2['plugins']:
           if (i.split(",")[0] == j['shortName'] and i.split(",")[1].strip() != j['version']):        
               print("Not Matched due to version---  "+i.split(",")[0] +"   Gold Copy Instance version :-- "+ i.split(",")[1].strip()+ "   Remote Jenkins Instance version :-- "+ j['version'])
               f2.write(i.split(",")[0]+","+i.split(",")[1].strip()+","+j['version']+'\n')
               count2+=1
   
   print("-----------------------------------------------------------------")
   print("Total Unmatched Plugins with different version is -- "+str(count2))
   print("-----------------------------------------------------------------")

   f2.write("\n------Plugin Unavailable-------\n")
   f2.write("Plugin Name"+"\n\n")
   # Loop for Unavailable Plugins
   for i in f[2:]:
       count1=0    
       for j in data2['plugins']:
           if (i.split(",")[0] == j['shortName']):
               count1=1
       if count1 == 0:         
           print ("Not Available on Remote Instance--- "+ i.split(",")[0])
           f2.write(i.split(",")[0]+"\n")
           count3+=1
   f1.close()
   f2.close()
   print("-----------------------------------------------------------------")
   print("Total Unavailable Plugins  -- "+str(count3))
   print("-----------------------------------------------------------------")


def match_shared_libraries(master,remote,remote_host,remote_user,remote_password):  
   master_home = master.run_script('println(System.getenv("JENKINS_HOME"))')
   remote_home = remote.run_script('println(System.getenv("JENKINS_HOME"))')    
   gsl1 = ET.parse(master_home+'/org.jenkinsci.plugins.workflow.libs.GlobalLibraries.xml').getroot()
   ssh = pxssh.pxssh()
   ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
   ssh.sendline('sudo cat '+remote_home+'/org.jenkinsci.plugins.workflow.libs.GlobalLibraries.xml') 
   ssh.prompt() # match the prompt
   xmlstr = str("".join((ssh.before).split('\r\n')[1:]))
   ssh.logout()              
   gsl2 = ET.fromstring(xmlstr)
   print("----------GLOBAL SHARED LIBRARIES-------------------")
   f2 = open("report.csv","a")

   # Loop For finding Matched Global Shared Libraries
   f2.write("\n -------GLOBAL SHARED LIBRARIES MATCHED------------\n")
   f2.write("Library Name\n\n")        
   for i in gsl1.find('libraries').iter('org.jenkinsci.plugins.workflow.libs.LibraryConfiguration'):   
      for j in gsl2.find('libraries').iter('org.jenkinsci.plugins.workflow.libs.LibraryConfiguration'):
          if i.find('name').text == j.find('name').text and i.find('retriever').find('scm').find('remote').text == j.find('retriever').find('scm').find('remote').text:
             credential_id1 = i.find('retriever').find('scm').find('credentialsId').text
             credential_id2 = j.find('retriever').find('scm').find('credentialsId').text
             cr1 = ET.parse(master_home+'/credentials.xml').getroot()
             for z in cr1.find('domainCredentialsMap').find('entry').find('java.util.concurrent.CopyOnWriteArrayList').iter('com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl'):
                if credential_id1 == z.find('id').text:
                   data = 'println(hudson.util.Secret.decrypt("{}"))'.format(z.find('password').text)
                   p1 = master.run_script(data)
                   user1 = z.find('username').text

             ssh = pxssh.pxssh()
             ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
             ssh.sendline('sudo cat '+remote_home+'/credentials.xml')
             ssh.prompt()
             xmlstr1 =  str("".join((ssh.before).split('\r\n')[1:]))
             ssh.logout()
             cr2 = ET.fromstring(xmlstr1)
             for z in cr2.find('domainCredentialsMap').find('entry').find('java.util.concurrent.CopyOnWriteArrayList').iter('com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl'):
                if credential_id2 == z.find('id').text:     
                   data = 'println(hudson.util.Secret.decrypt("{}"))'.format(z.find('password').text)
                   p2 = remote.run_script(data)
                   user2 = z.find('username').text
             if user1 == user2 and p1 == p2:   
                print("Global Shared Library Matched  --->" +i.find('name').text)
                f2.write(i.find('name').text+'\n')

   f2.write("\n -------GLOBAL SHARED LIBRARIES UNMATCHED DUE TO CREDENTIALS------------\n")
   f2.write("Library Name\n\n")     
   # Global Shared Library unmatched due to different credentials
   for i in gsl1.find('libraries').iter('org.jenkinsci.plugins.workflow.libs.LibraryConfiguration'):   
      for j in gsl2.find('libraries').iter('org.jenkinsci.plugins.workflow.libs.LibraryConfiguration'):
          if i.find('name').text == j.find('name').text and i.find('retriever').find('scm').find('remote').text == j.find('retriever').find('scm').find('remote').text:
             credential_id1 = i.find('retriever').find('scm').find('credentialsId').text
             credential_id2 = j.find('retriever').find('scm').find('credentialsId').text
             cr1 = ET.parse(master_home+'/credentials.xml').getroot()
             for z in cr1.find('domainCredentialsMap').find('entry').find('java.util.concurrent.CopyOnWriteArrayList').iter('com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl'):
                if credential_id1 == z.find('id').text:
                   data = 'println(hudson.util.Secret.decrypt("{}"))'.format(z.find('password').text)
                   p1 = master.run_script(data)
                   user1 = z.find('username').text

             ssh = pxssh.pxssh()
             ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
             ssh.sendline('sudo cat '+remote_home+'/credentials.xml')
             ssh.prompt()
             xmlstr1 =  str("".join((ssh.before).split('\r\n')[1:]))
             ssh.logout()
             cr2 = ET.fromstring(xmlstr1)
             for z in cr2.find('domainCredentialsMap').find('entry').find('java.util.concurrent.CopyOnWriteArrayList').iter('com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl'):
                if credential_id2 == z.find('id').text:     
                   data = 'println(hudson.util.Secret.decrypt("{}"))'.format(z.find('password').text)
                   p2 = remote.run_script(data)
                   user2 = z.find('username').text
             if user1 != user2 or p1 == p2:   
                print("Global Shared Library UnMatched due to different credentials ---> " +i.find('name').text)
                f2.write(i.find('name').text+'\n')


   f2.write("\n -------GLOBAL SHARED LIBRARIES UNMATCHED DUE TO Remote URL------------\n")
   f2.write("Library Name,Gold Copy Instance Url,Remote Jenkins Url\n\n")             
   # Loop for unmatched Global Shared Libraries due to different remote 
   for i in gsl1.find('libraries').iter('org.jenkinsci.plugins.workflow.libs.LibraryConfiguration'):   
      for j in gsl2.find('libraries').iter('org.jenkinsci.plugins.workflow.libs.LibraryConfiguration'):                
          if i.find('name').text == j.find('name').text and i.find('retriever').find('scm').find('remote').text != j.find('retriever').find('scm').find('remote').text:
                print("Global Shared Library UnMatched due to different remote ---> "+i.find('name').text+"  Gold Copy Remote URL -- "+i.find('retriever').find('scm').find('remote').text+" Remote Master URL  -- "+j.find('retriever').find('scm').find('remote').text)
                f2.write(i.find('name').text+","+i.find('retriever').find('scm').find('remote').text+","+j.find('retriever').find('scm').find('remote').text+'\n')

   f2.write("\n------GLOBAL SHARED LIBRARIES UNAVAILABLE--------\n")
   f2.write("Library Name \n\n")
   for i in gsl1.find('libraries').iter('org.jenkinsci.plugins.workflow.libs.LibraryConfiguration'):
      count = 0        
      for j in gsl2.find('libraries').iter('org.jenkinsci.plugins.workflow.libs.LibraryConfiguration'):                         
          if i.find('name').text == j.find('name').text:
                count = 1
      if count == 0:
         print("Global Shared Library Unavailable on Remote ---> "+i.find('name').text)
         f2.write(i.find('name').text+'\n') 
   f2.close()  

def match_github_servers(master,remote,remote_host,remote_user,remote_password):
   master_home = master.run_script('println(System.getenv("JENKINS_HOME"))')
   remote_home = remote.run_script('println(System.getenv("JENKINS_HOME"))')
   g1 = ET.parse(master_home+'/github-plugin-configuration.xml').getroot()
   ssh = pxssh.pxssh()
   ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
   ssh.sendline('sudo cat '+remote_home+'/github-plugin-configuration.xml') 
   ssh.prompt() # match the prompt
   xmlstr = str("".join((ssh.before).split('\r\n')[1:]))
   ssh.logout()              
   g2 = ET.fromstring(xmlstr)
   print("----------GITHUB SERVERS-------------------")
   f2 = open("report.csv","a")

   # Loop for matching Github Servers
   f2.write("\n -------GITHUB SERVERS MATCHED------------\n")  
   f2.write("Server Name \n\n")    
   for i in g1.find('configs').iter('github-server-config'):
      for j in g2.find('configs').iter('github-server-config'):
         if i.find('name').text == j.find('name').text and i.find('apiUrl').text == j.find('apiUrl').text:           
            print("Github Server Matched --->  "+ i.find('name').text)
            f2.write(i.find('name').text+'\n')

   # Loop for unmatched Github Servers due to different apiUrl
   f2.write("\n -------GITHUB SERVERS UNMATCHED DUE TO API_URL------------\n")  
   f2.write("Server Name, GoldCopy apiUrl, Remote JenkinsapiUrl \n\n")    
   for i in g1.find('configs').iter('github-server-config'):
      for j in g2.find('configs').iter('github-server-config'):
         if i.find('name').text == j.find('name').text and i.find('apiUrl').text != j.find('apiUrl').text:           
            print("Github Server UnMatched due to apiUrl--->  "+ i.find('name').text+"Gold Copy aipUrl -- "+i.find('apiUrl').text+ "Renote Jenkins apiUrl -- "+j.find('apiUrl').text)
            f2.write(i.find('name').text+","+i.find('apiUrl').text+","+j.find('apiUrl').text+'\n')  

   # Loop for unavailable Github Servers                
   f2.write("\n -------GITHUB SERVERS UNAVIALABLE------------\n")  
   f2.write("Server Name \n\n")    
   for i in g1.find('configs').iter('github-server-config'):
      count = 0    
      for j in g2.find('configs').iter('github-server-config'):
         if i.find('name').text == j.find('name').text:           
            count = 1
      if count == 0:
         print("Github Server Unavailable --->  "+ i.find('name').text)
         f2.write(i.find('name').text+'\n')
   f2.close()

def check_maven_installations(master,remote,remote_host,remote_user,remote_password):
   #master_home = master.run_script('println(System.getenv("JENKINS_HOME"))')
   remote_home = remote.run_script('println(System.getenv("JENKINS_HOME"))')
   #m1 = ET.parse(master_home+'/hudson.tasks.Maven.xml').getroot()
   ssh = pxssh.pxssh()
   ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
   ssh.sendline('sudo cat '+remote_home+'/hudson.tasks.Maven.xml') 
   ssh.prompt() # match the prompt
   xmlstr = str("".join((ssh.before).split('\r\n')[1:]))
   ssh.logout()              
   m2 = ET.fromstring(xmlstr)
   print("----------Maven Installations-------------------")
   f2 = open("report.csv","a")
   
   # Loop for matching maven installations
   f2.write("\n -------Maven versions------------\n")  
   #for i in m1.find('installations').iter('hudson.tasks.Maven_-MavenInstallation'):
    #  count = 0    
   for i in m2.find('installations').iter('hudson.tasks.Maven_-MavenInstallation'):
         #if i.find('home').text == j.find('home').text:  
            ssh = pxssh.pxssh()
            ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
            ssh.sendline("python -c 'import os; print(os.path.exists("+'"'+i.find('home').text+'"'+"))'") 
            ssh.prompt() # match the prompt
            val = str("".join((ssh.before).split('\r\n')[1:]))
            ssh.logout()
            if val == "True":     
               print("Maven version exists locally  --> "+i.find('home').text)
               f2.write("Maven version exists locally ---> "+","+i.find('home').text+'\n')
            else:
               print("Maven version does NOT exists locally  --> "+i.find('home').text)
               f2.write("Maven version does NOT exists locally ---> "+","+i.find('home').text+'\n')                     
            
                  
def match_sonar_servers(master,remote,remote_host,remote_user,remote_password):
   master_home = master.run_script('println(System.getenv("JENKINS_HOME"))')
   remote_home = remote.run_script('println(System.getenv("JENKINS_HOME"))')
   s1 = ET.parse(master_home+'/hudson.plugins.sonar.SonarGlobalConfiguration.xml').getroot()
   ssh = pxssh.pxssh()
   ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
   ssh.sendline('sudo cat '+remote_home+'/hudson.plugins.sonar.SonarGlobalConfiguration.xml') 
   ssh.prompt() # match the prompt
   xmlstr = str("".join((ssh.before).split('\r\n')[1:]))
   ssh.logout()              
   s2 = ET.fromstring(xmlstr)
   print("----------Sonar Servers-------------------")
   f2 = open("report.csv","a")

   # Loop for matching Sonar Servers
   f2.write("\n -------Sonar Servers------------\n\n")
   for i in s1.find('installations').iter('hudson.plugins.sonar.SonarInstallation'):
      count = 0  
      for j in s2.find('installations').iter('hudson.plugins.sonar.SonarInstallation'):
          if i.find('name').text == j.find('name').text and i.find('serverUrl').text == j.find('serverUrl').text:
             credential_id1 = i.find('credentialsId').text
             credential_id2 = j.find('credentialsId').text
             cr1 = ET.parse(master_home+'/credentials.xml').getroot()
             for z in cr1.find('domainCredentialsMap').find('entry').find('java.util.concurrent.CopyOnWriteArrayList').iter('org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl'):
                if credential_id1 == z.find('id').text:
                   data = 'println(hudson.util.Secret.decrypt("{}"))'.format(z.find('secret').text)
                   p1 = master.run_script(data)

             ssh = pxssh.pxssh()
             ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
             ssh.sendline('sudo cat '+remote_home+'/credentials.xml')
             ssh.prompt()
             xmlstr1 =  str("".join((ssh.before).split('\r\n')[1:]))
             ssh.logout()
             cr2 = ET.fromstring(xmlstr1)
             p2 = ""
             for z in cr2.find('domainCredentialsMap').find('entry').find('java.util.concurrent.CopyOnWriteArrayList').iter('org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl'):
                if credential_id2 == z.find('id').text:     
                   data = 'println(hudson.util.Secret.decrypt("{}"))'.format(z.find('secret').text)
                   p2 = remote.run_script(data)
             if p1 == p2:   
                print("Sonar Server Matched  ---> "+i.find('name').text)
                f2.write("Sonar Server Matched  ---> "+","+i.find('name').text+'\n')
             else:
                print("Sonar Server UnMatched due to credentials---> "+i.find('name').text)
                f2.write("Sonar Server UnMatched due to credentials ---> "+","+i.find('name').text+'\n')
          if i.find('name').text == j.find('name').text and i.find('serverUrl').text != j.find('serverUrl').text:
             print("Sonar Server Unmatched due to different Urls --> "+i.find('name').text+"Gold Copy Url -- "+i.find('serverUrl').text+"Remote Jenkins Url -- "+j.find('serverUrl').text)       
             f2.write("Sonar Server Unmatched due to different Urls --> "+i.find('name').text+","+"Gold Copy Url -- "+i.find('serverUrl').text+","+"Remote Jenkins Url -- "+j.find('serverUrl').text+'\n')       
          if i.find('name').text == j.find('name').text:
             count = 1
      if count == 0:
         print("Sonar Server Unavailable --> "+ i.find('name').text)          
         f2.write("Sonar Server Unavailable --> "+","+ i.find('name').text+'\n')
   f2.close()

def verify_security(master,remote):
       info1 = master.get_info()
       info2 = remote.get_info()
       f2 = open('report.csv','a')
       print("------Security-----------")
       f2.write("\n---------Security---------\n\n") 
       if info1['useSecurity'] == info2['useSecurity']:
          print("Security is Enabled on Both")
          f2.write("Security is Enabled on Both\n")
       else:
          print("Security is NOT matching"+"Gold Copy Master -- "+info1['useSecurity']+"Remote Jenkins -- "+info2['useSecurity']) 
          f2.write("Security is NOT matching"+","+"Gold Copy Master -- "+info1['useSecurity']+","+"Remote Jenkins -- "+info2['useSecurity']+'\n') 
       f2.close()

def main(): 
   if len(sys.argv) != 10:
        check()
   # Function to save GoldCopy Jenkins Instance Plugins Information to csv file 
   save_goldcopy_info(sys.argv[1],sys.argv[2],sys.argv[3])
   # Function to match the csv file with Remote Jenkins Instance Plugin Configuration
   match_plugins(sys.argv[4],sys.argv[5],sys.argv[6])
   
   # Calling the jenkins using api
   goldcopy = jenkins.Jenkins(sys.argv[1],sys.argv[2],sys.argv[3])
   remotemaster = jenkins.Jenkins(sys.argv[4],sys.argv[5],sys.argv[6])     
   # Function to match Global Shared Libraries
   match_shared_libraries(goldcopy,remotemaster,sys.argv[7],sys.argv[8],sys.argv[9])

   # Function to match github servers
   match_github_servers(goldcopy,remotemaster,sys.argv[7],sys.argv[8],sys.argv[9])

   #Function to check Maven Installations
   check_maven_installations(goldcopy,remotemaster,sys.argv[7],sys.argv[8],sys.argv[9])

   #Function to match Sonar Servers
   match_sonar_servers(goldcopy,remotemaster,sys.argv[7],sys.argv[8],sys.argv[9])

   #Function to verify security
   verify_security(goldcopy,remotemaster)

if __name__ == '__main__':
   main()
