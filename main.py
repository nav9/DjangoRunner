'''
Django Runner: A simple program to manage various Django tasks
Created on 24-Apr-2021
@author: Navin
License: MIT
'''

import os
import shutil #for moving file
import pickle
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
#         self.FULL_FOLDER_PATH = 0
#         #self.SUBDIRECTORIES = 1
#         self.FILES_IN_FOLDER = 2
#     
#     """ Get names of files in each folder and subfolder. Also get sizes of files """
#     def getFileNamesOfFilesInAllFoldersAndSubfolders(self, folderToConsider): 
#         #TODO: check if folder exists, what about symlinks?, read-only files, files without permission to read, files that can't be moved, corrupted files, What about "file-like objects", Encrypted containers?
#         folderPaths = []; filesInFolder = []; fileSizes = []
#         result = os.walk(folderToConsider)        
#         for oneFolder in result:
#             folderPath = self.folderSlash(oneFolder[self.FULL_FOLDER_PATH])
#             folderPaths.append(folderPath)
#             #subdir = oneFolder[self.SUBDIRECTORIES]
#             filesInThisFolder = oneFolder[self.FILES_IN_FOLDER]
#             sizeOfFiles = []
#             for filename in filesInThisFolder:
#                 fileProperties = os.stat(folderPath + filename)
#                 sizeOfFiles.append(fileProperties.st_size)
#             fileSizes.append(sizeOfFiles)
#             filesInFolder.append(filesInThisFolder)            
#         return folderPaths, filesInFolder, fileSizes #returns as [fullFolderPath1, fullFolderPath2, ...], [[filename1, filename2, filename3, ...], [], []], [[filesize1, filesize2, filesize3, ...], [], []]
   
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
        self.PROJECT_FOLDERS_FILENAME = "projectFolders.pickle"
        self.RECENT_FOLDER = "RecentFolder"
        self.OTHER_DJANGO_PROJECTS = "OtherProjects"
        self.djangoProjectFolders = {} #stores the most recent project folder and other known folders
        
    def loadParameters(self):
        #---load project folder names
        if self.fileOps.isValidFile(self.PROJECT_FOLDERS_FILENAME):#if file exists, load data
            self.djangoProjectFolders = self.fileOps.unPickleThis(self.PROJECT_FOLDERS_FILENAME)
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
            if invalidFolderDetected:
                self.fileOps.pickleThis(self.djangoProjectFolders, self.PROJECT_FOLDERS_FILENAME)            
        else:
            print('No known Django folders stored.')
    
    def getProjectFolderPath(self):
        return self.djangoProjectFolders[self.RECENT_FOLDER]
    
    def setProjectFolderPath(self, fullFolderPath):
        newPaths = set()
        newPaths.add(fullFolderPath)
        if not self.djangoProjectFolders:#create the dict
            self.djangoProjectFolders = {self.PROJECT_FOLDERS_FILENAME: fullFolderPath, self.OTHER_DJANGO_PROJECTS: newPaths}
        else:#add to existing set of folders and make new folder the default
            self.djangoProjectFolders[self.PROJECT_FOLDERS_FILENAME] = fullFolderPath
            self.djangoProjectFolders[self.OTHER_DJANGO_PROJECTS].add(fullFolderPath)
        self.fileOps.pickleThis(self.djangoProjectFolders, self.PROJECT_FOLDERS_FILENAME)
        print("Saved folder path ", fullFolderPath)
        
#-----------------------------------------------             
#-----------------------------------------------
#-------------------- MENUS --------------------
#-----------------------------------------------
#-----------------------------------------------
class MainMenu:#Commandline
    def __init__(self):
        self.options = [
            "Create a new Django project",
            "Select an existing Django project folder",
            "Create an app in selected Django project"
            ""
            ]
    
    def showMenuAndGetInput(self):
        pass
        
class MenuController:#Commandline
    def __init__(self):
        parameters = ProgramParameters()
        parameters.loadParameters()      
        if not parameters.djangoProjectFolders:#is empty (no known Django project)
            #---get Django project folder path from user since none is known
            folderChoice = FolderChoiceMenu()
            folderChoice.showUserTheMenu(["Please select the Django project folder"], ["Please specify the root folder of the project"])
            folderNameWithPath = folderChoice.getUserChoice()
            if not folderNameWithPath:
                print('No Django folder specified. Exiting...')
                exit()
            else:
                parameters.setProjectFolderPath(folderNameWithPath)
        else:
            print("\n\nDjango project considered: ", parameters.getProjectFolderPath())
            print("You can change the project using the menu options below")          
     
    def run(self):
        pass        
     
     
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
           

#-----------------------------------------------             
#-----------------------------------------------
#------------ PROGRAM STARTS HERE --------------
#-----------------------------------------------
#-----------------------------------------------
if __name__ == '__main__':
    sg.theme('Dark grey 13')  #GUI's theme

    menu = MenuController()
    menu.run()
        
               
        
    

