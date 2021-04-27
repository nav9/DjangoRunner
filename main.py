#!/usr/bin/env python
'''
Django Runner: A simple program to manage various Django tasks
Created on 24-Apr-2021
@author: Navin
License: MIT
'''

import os
import shlex #split string like the shell's split mechanism
import shutil #for moving file
import pickle #for saving data
import subprocess #for running processes outside this program
import PySimpleGUI as sg


#-----------------------------------------------             
#-----------------------------------------------
#------------------ FILE OPS -------------------
#-----------------------------------------------
#-----------------------------------------------

class GlobalConstants:
    EVENT_CANCEL = 'Cancel'
    EVENT_EXIT = 'Cancel'
    YES_BUTTON = 'Yes'
    NO_BUTTON = 'No'
    
class FileOperations:
    def __init__(self):
        pass
   
    def isValidFile(self, filenameWithPath):#used to check if file exists, without throwing exception
        return os.path.isfile(filenameWithPath)   
    
    def getFilenameAndExtension(self, filenameOrPathWithFilename):
        filename, fileExtension = os.path.splitext(filenameOrPathWithFilename)
        return filename, fileExtension
    
    def deleteFile(self, filenameWithPath):
        os.remove(filenameWithPath) #TODO: check if file exists before deleting
        
    def writeLinesToFile(self, filenameWithPath, report):
        fileHandle = open(filenameWithPath, 'w')
        for line in report:
            fileHandle.write(line)
            fileHandle.write("\n")
        fileHandle.close()
        
    def readFromFile(self, filenameWithPath):
        with open(filenameWithPath) as f:
            lines = f.read().splitlines()#TODO: try catch
        return lines              
    
    def createDirectoryIfNotExisting(self, folder):
        if not os.path.exists(folder): 
            try: os.makedirs(folder)
            except FileExistsError:#in case there's a race condition where some other process creates the directory before makedirs is called
                pass
    
    def isThisValidDirectory(self, folderpath):
        return os.path.exists(folderpath)

    """ Move file to another directory. Renaming while moving is possible """
    def moveFile(self, existingPath, existingFilename, newPath, newFilename):
        shutil.move(existingPath + existingFilename, newPath + newFilename)    
    
    """ Adds a slash at the end of the folder name if it isn't already present """
    def folderSlash(self, folderNameWithPath):
        if folderNameWithPath.endswith('/') == False: 
            folderNameWithPath = folderNameWithPath + '/' 
        return folderNameWithPath
    
    """ Writes a datastructure to a pickle file. Overwrites old file by default """
    def pickleThis(self, datastructure, filename):
        fHandle = open(filename, "wb") #TODO: try-catch   
        pickle.dump(datastructure, fHandle)
        fHandle.close()
        
    """ Reads a datastructure from a pickle file """
    def unPickleThis(self, filename):
        fHandle = open(filename, "rb") #TODO: try-catch   
        datastructure = pickle.load(fHandle)
        fHandle.close() 
        return datastructure   
    

#-----------------------------------------------             
#-----------------------------------------------
#----------------- PARAMETERS ------------------
#-----------------------------------------------
#-----------------------------------------------
class ProgramParameters:
    def __init__(self):
        self.fileOps = FileOperations()
        self.PROJECT_FOLDERS_PICKLE_FILENAME = "projectFolders.pickle"
        self.RECENT_FOLDER = "RecentFolder"
        self.OTHER_DJANGO_PROJECTS = "OtherProjects"
        self.djangoProjectFolders = {} #stores the most recent project folder and other known folders
        
    def loadParameters(self):
        #---load project folder names
        if self.fileOps.isValidFile(self.PROJECT_FOLDERS_PICKLE_FILENAME):#if file exists, load data
            self.djangoProjectFolders = self.fileOps.unPickleThis(self.PROJECT_FOLDERS_PICKLE_FILENAME)
            #---check if folders are still valid. Remove invalid ones
            folders = self.djangoProjectFolders[self.OTHER_DJANGO_PROJECTS]
            validFolders = set()
            invalidFolderDetected = False
            for folder in folders:
                if self.fileOps.isThisValidDirectory(folder): 
                    validFolders.add(folder)
                else: 
                    invalidFolderDetected = True
                    print('WARNING: This folder does not exist. Removing from stored list of folders: ', folder)
                    if folder == self.djangoProjectFolders[self.RECENT_FOLDER]:#recent folder is no longer valid and got removed
                        self.djangoProjectFolders[self.RECENT_FOLDER] = None
            self.djangoProjectFolders[self.OTHER_DJANGO_PROJECTS] = validFolders
            if self.djangoProjectFolders[self.RECENT_FOLDER] == None:
                if not self.djangoProjectFolders[self.OTHER_DJANGO_PROJECTS]:#no valid folders present
                    self.djangoProjectFolders = {}
                else:#take the first available folder as the default
                    for folder in self.djangoProjectFolders[self.OTHER_DJANGO_PROJECTS]:
                        self.djangoProjectFolders[self.RECENT_FOLDER] = folder
                        print('Making this folder the default: ', folder)
                        break
            else:#recent folder is valid
                os.chdir(self.djangoProjectFolders[self.RECENT_FOLDER])#make this the current folder
                print('Changed current working directory to: ', self.djangoProjectFolders[self.RECENT_FOLDER])
            if invalidFolderDetected:
                self.fileOps.pickleThis(self.djangoProjectFolders, self.PROJECT_FOLDERS_PICKLE_FILENAME)            
        else:
            print('No known Django folders stored.')
    
    def getProjectFolderPath(self):
        return self.djangoProjectFolders[self.RECENT_FOLDER]
    
    def setProjectFolderPath(self, fullFolderPath):
        newPaths = set()
        newPaths.add(fullFolderPath)
        if not self.djangoProjectFolders:#create the dict
            self.djangoProjectFolders = {self.RECENT_FOLDER: fullFolderPath, self.OTHER_DJANGO_PROJECTS: newPaths}
        else:#add to existing set of folders and make new folder the default
            self.djangoProjectFolders[self.RECENT_FOLDER] = fullFolderPath
            self.djangoProjectFolders[self.OTHER_DJANGO_PROJECTS].add(fullFolderPath)
        self.fileOps.pickleThis(self.djangoProjectFolders, self.PROJECT_FOLDERS_PICKLE_FILENAME)        
        print("Saved this folder path as a known Django project ", fullFolderPath)
        os.chdir(fullFolderPath)
        print("Changed current working directory to: ", fullFolderPath)
        
#-----------------------------------------------             
#-----------------------------------------------
#-------------------- MENUS --------------------
#-----------------------------------------------
#-----------------------------------------------

class MenuResponses:#For having common return values between main menu and sub menus. Every submenu which needs to return some data to main menu can return a MenuResponse object
    def __init__(self):        
        self.NEW_DJANGO_PROJECT_FOLDER_SELECTED = 'newProjectFolderCreated'
        self.DJANGO_PROJECT_FOLDER_NAME_WITH_PATH = "folderNameWithPath"
        #Each submenu that needs to return some value would have to return a unique response key. That's
        #how the main menu will know which submenu response is being returned, and the main menu will be
        #able to use if then statements to perform appropriate actions. 
        self.response = {
                         self.NEW_DJANGO_PROJECT_FOLDER_SELECTED: None,
                         self.DJANGO_PROJECT_FOLDER_NAME_WITH_PATH: None,
                        }
        
class UserInput:#To ask the user for a valid integer in the range of the menu ordinals displayed
    def __init__(self, options):
        self.options = options
        
    def getInput(self):        
        i = 1
        for option in self.options:#display menu options with ordinals
            print(str(i)+".", option.optionName)
            i = i + 1
        choice = input("Your choice (enter a number)? ")
        if choice.isdigit():#only True for whole numbers
            choice = int(choice)
            if choice <= 0 or choice > i-1:
                choice = None
        else:
            choice = None
        if choice == None: print("Please enter a valid input")
        else: choice = choice - 1 #since the first position in a list is 0
        return choice 
    
class FolderChoiceMenu:#GUI
    def __init__(self):
        self.event = None
        self.values = None
        self.horizontalSepLen = 35       
    
    def showUserTheMenu(self, topText, bottomText):
        layout = []
        for s in topText:
            layout.append([sg.Text(s, justification='left')])
        layout.append([sg.Input(), sg.FolderBrowse()])
        for s in bottomText:
            layout.append([sg.Text(s, text_color='grey', justification='left')])        
        layout.append([sg.Text('_' * self.horizontalSepLen, justification='right', text_color='black')])
        layout.append([sg.Button(GlobalConstants.EVENT_CANCEL), sg.Button('Ok')])
        
        window = sg.Window('', layout, grab_anywhere=False, element_justification='right')    
        self.event, self.values = window.read()        
        window.close()
    
    def getUserChoice(self):
        retVal = None
        if self.event == sg.WIN_CLOSED or self.event == GlobalConstants.EVENT_EXIT or self.event == GlobalConstants.EVENT_CANCEL or self.values[0] == '':
            pass #retVal is already None
        else:
            fileOps = FileOperations()
            folderChosen = self.values[0]
            if fileOps.isThisValidDirectory(folderChosen):#this check is not really required
                retVal = fileOps.folderSlash(folderChosen)
        return retVal
    
class Exit_SubMenu:
    def __init__(self):
        self.optionName = "Exit"
    def execute(self):
        print('Exiting program...')
        exit()
        
class CommandlineExecutor:
    def __init__(self, command):
        self.command = command
    
    def executeCommand(self):
        #command = ['django-admin', 'startproject', projectName]
        #subprocess.check_call(command)
        #subprocess.check_call(shlex.split(command))
        process = subprocess.Popen(shlex.split(self.command), stdout=subprocess.PIPE) #TODO: implement error handling
        output, error = process.communicate()
        print("Output: ", output)
        print("Error: ", error)  
        
    def executeCommandAndDetach(self):
        subprocess.Popen(shlex.split(self.command), close_fds=True)       
        
class CreateDjangoProject_SubMenu:#ask user to show the root folder of a Django project
    def __init__(self, topText, bottomText):
        self.optionName = "Create a new Django project"
        self.topText = topText
        self.bottomText = bottomText
    
    def execute(self):
        folderChoice = FolderChoiceMenu()
        folderChoice.showUserTheMenu(self.topText, self.bottomText)
        folderNameWithPath = folderChoice.getUserChoice() #TODO: check if name given by user is valid
        folderSuccessfullyCreated = None
        if not folderNameWithPath:
            folderNameWithPath = None
            print('No Django folder specified.')
        else:
            folderSuccessfullyCreated = self.__createDjangoProject__(folderNameWithPath)
        rval = MenuResponses()
        rval.response[rval.DJANGO_PROJECT_FOLDER_NAME_WITH_PATH] = folderNameWithPath
        rval.response[rval.NEW_DJANGO_PROJECT_FOLDER_SELECTED] = folderSuccessfullyCreated 
        return rval
    
    def __createDjangoProject__(self, folderNameWithPath):
        projectCreated = False
        projectName = input("\nWhat name would you like to give your project (simply press Enter if you want to exit)? ")
        if projectName:#TODO: check if name given by user is valid
            os.chdir(folderNameWithPath)
            print("Changed working directory to: ", os.getcwd())
            #---create the Django project
            cmd = CommandlineExecutor('django-admin startproject ' + projectName)
            cmd.executeCommand()
            #TODO: verify that it is created. Errorhandling
            projectCreated = True
        else:
            projectName = None
        return projectCreated
        

class SelectDjangoFolder_SubMenu:#ask user to show the root folder of a Django project
    def __init__(self, topText, bottomText):
        self.optionName = "Select existing Django project folder"
        self.topText = topText
        self.bottomText = bottomText
    
    def execute(self):
        folderChoice = FolderChoiceMenu()
        folderChoice.showUserTheMenu(self.topText, self.bottomText)
        folderNameWithPath = folderChoice.getUserChoice()
        folderSpecified = True
        if not folderNameWithPath:
            folderNameWithPath = None
            folderSpecified = False
            print('No Django folder specified.')
        rval = MenuResponses()
        rval.response[rval.DJANGO_PROJECT_FOLDER_NAME_WITH_PATH] = folderNameWithPath
        rval.response[rval.NEW_DJANGO_PROJECT_FOLDER_SELECTED] = folderSpecified
        return rval
    
class RunServer_SubMenu:
    def __init__(self):
        self.optionName = "Run the default server"
        self.commandToRun = "python manage.py runserver &"
    
    def execute(self):    
        print("Running default server...")
#         cmd = CommandlineExecutor(self.commandToRun)
#         cmd.executeCommandAndDetach()
        #os.spawnl(os.P_NOWAITO, 'some_long_running_command')
        os.system(self.commandToRun)

 
class MainMenu:#Commandline
    def __init__(self):
        #---submenus
        self.folderCreation = CreateDjangoProject_SubMenu(["Select folder in which you want to create your Django project"], ["Please specify the root folder of the project"])#The lists allow showing multiple lines of text in the GUI
        self.folderSelection = SelectDjangoFolder_SubMenu(["Select existing project folder"], ["Please specify the root folder of the project"])#The lists allow showing multiple lines of text in the GUI
        self.runServer = RunServer_SubMenu()
        self.exitOption = Exit_SubMenu() 
        #---menu options
        self.options = [] 
        #---program parameters
        self.parameters = ProgramParameters()
        self.parameters.loadParameters() #this function will also check existing folder paths to see if they are still valid, and remove invalid folders
        
        if not self.parameters.djangoProjectFolders:#is empty (no known Django project)
            self.__setMenuForNoKnownDjangoProjectMode__()                   
        else:
            self.__setMenuForNormalMode__()
            print("\n\nDjango project considered: ", self.parameters.getProjectFolderPath())
            print("You can change the current project using the menu options below.")          
    
    def execute(self):      
        while True:#keep showing main menu until exit
            menuName = "\nMain Menu";print(menuName);print(len(menuName)*'-')
            userInput = UserInput(self.options)               
            choice = userInput.getInput()
            returnVal = self.options[choice].execute()#invoke the sub-menu from one of the objects of sub-menus stored in self.options
            if not None: #some data is returned by the submenu
                #---perform action based on the type of data being returned
                if returnVal.response[returnVal.NEW_DJANGO_PROJECT_FOLDER_SELECTED] == True:
                    self.__setMenuForNormalMode__()
                    self.parameters.setProjectFolderPath(returnVal.response[returnVal.DJANGO_PROJECT_FOLDER_NAME_WITH_PATH])#register the newly created project
    
    def __setMenuForNoKnownDjangoProjectMode__(self):
        self.options = [self.folderCreation, self.folderSelection, self.exitOption]
        
    def __setMenuForNormalMode__(self):
        self.options = [self.runServer, self.folderCreation, self.folderSelection, self.exitOption]                   
    


#-----------------------------------------------             
#-----------------------------------------------
#------------ PROGRAM STARTS HERE --------------
#-----------------------------------------------
#-----------------------------------------------
if __name__ == '__main__':
    sg.theme('Dark grey 13')  #GUI's theme

    menu = MainMenu()
    menu.execute()
        
               
        
    

