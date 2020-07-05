import jarray
import inspect
import os
import subprocess
import json

from javax.swing import JCheckBox
from javax.swing import JButton
from javax.swing import JRadioButton
from javax.swing import ButtonGroup
from javax.swing import JTextField
from javax.swing import JLabel
from javax.swing import BoxLayout
from javax.swing import ImageIcon
from java.awt import GridLayout
from java.awt import GridBagLayout
from java.awt import GridBagConstraints
from javax.swing import JPanel
from javax.swing import JScrollPane
from javax.swing import JFileChooser
from javax.swing import JOptionPane
from javax.swing import JComponent
from javax.swing import JTextField
from javax.swing import JList
from javax.swing import JFrame
from javax.swing import ListSelectionModel
from javax.swing import DefaultListModel
from javax.swing import SwingUtilities
from javax.swing.filechooser import FileNameExtensionFilter
from java.awt.event import KeyListener
from java.awt.event import KeyEvent
from java.awt.event import KeyAdapter
from java.awt import Dimension
from javax.swing.event import DocumentEvent
from javax.swing.event import DocumentListener
from javax.swing import BorderFactory

from java.lang import Class
from java.lang import System
from java.lang import Runnable
from java.sql  import DriverManager, SQLException
from java.util.logging import Level
from java.io import File
from org.sleuthkit.datamodel import SleuthkitCase
from org.sleuthkit.datamodel import AbstractFile
from org.sleuthkit.datamodel import ReadContentInputStream
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
from org.sleuthkit.autopsy.ingest import IngestModule
from org.sleuthkit.autopsy.ingest.IngestModule import IngestModuleException
from org.sleuthkit.autopsy.ingest import DataSourceIngestModule
from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
from org.sleuthkit.autopsy.ingest import GenericIngestModuleJobSettings
from org.sleuthkit.autopsy.ingest import IngestModuleIngestJobSettingsPanel
from org.sleuthkit.autopsy.ingest import IngestMessage
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.autopsy.ingest import ModuleDataEvent
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.coreutils import PlatformUtil
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.casemodule.services import Services
from org.sleuthkit.autopsy.casemodule.services import FileManager
from org.sleuthkit.autopsy.casemodule.services import Blackboard
from org.sleuthkit.autopsy.datamodel import ContentUtils


# Factory that defines the name and details of the module and allows Autopsy
# to create instances of the modules that will do the analysis.
class DoiDataSourceIngestModuleFactory(IngestModuleFactoryAdapter):

    def __init__(self):
        self.settings = None

    moduleName = "Detection of Objects in Images"
    
    def getModuleDisplayName(self):
        return self.moduleName
    
    def getModuleDescription(self):
        return "DOI Forensics - Detection of Objects in Images"
    
    def getModuleVersionNumber(self):
        return "1.0"
        
    def getDefaultIngestJobSettings(self):
        return GenericIngestModuleJobSettings()

    def hasIngestJobSettingsPanel(self):
        return True

    def getIngestJobSettingsPanel(self, settings):
        if not isinstance(settings, GenericIngestModuleJobSettings):
            raise IllegalArgumentException("Expected settings argument to be instanceof GenericIngestModuleJobSettings")
        self.settings = settings
        return DoiDataSourceIngestModuleGUISettingsPanel(self.settings)

    def isDataSourceIngestModuleFactory(self):
        return True

    def createDataSourceIngestModule(self, ingestOptions):
        return DoiDataSourceIngestModule(self.settings)


# Data Source-level ingest module.  One gets created per data source.
class DoiDataSourceIngestModule(DataSourceIngestModule):

    _logger = Logger.getLogger(DoiDataSourceIngestModuleFactory.moduleName)

    _supported_images_types = [#'application/octet-stream', # DIB, SUN
                                #'video/quicktime', # HEIC/HEIF
                                'image/tiff', # TIFF
                                'image/bmp', # BMP
                                'image/gif', # GIF
                                'image/x-portable-graymap', # PGM
                                'image/png', # PNG
                                'image/x-tga', # TGA
                                'image/x-rgb', # SGI
                                'image/webp', # WEBP
                                'image/x-portable-pixmap', # PPM
                                'image/jp2', # JPEG2000
                                'image/jpeg', # JPEG
                                'image/vnd.zbrush.pcx', # PCX
                                'image/x-portable-bitmap', # PBM
                                'image/x-xbitmap' # XBM
                                ]

    CONFIDENCE_ATTR_TYPE_NAME = 'DOI_BEST_CONFIDENCE'
    RESULT_ATTR_TYPE_NAME = 'DOI_IMAGE_RESULT'
    CLASS_ATTR_TYPE_NAME = 'DOI_CLASS'
    DOI_ARTIFACT_TYPE_NAME = 'DOI_OBJECT_DETECTED'

    MIN_FILE_SIZE = 5120

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    def __init__(self, settings):
        self.context = None
        self.local_settings = settings

    def startUp(self, context):
        
        if not PlatformUtil.isWindowsOS():
            raise IngestModuleException('Right now, this module only supports Windows')
        
        # Checking for necessary files
        module_path = os.path.dirname(os.path.abspath(__file__))
        self.path_to_exe = os.path.join(module_path, 'doi.exe')
        if not os.path.exists(self.path_to_exe):
            raise IngestModuleException('Executable file not found!')
        path_to_config = os.path.join(module_path, 'config')
        if not os.path.exists(path_to_config):
            raise IngestModuleException('Config directory not found!')

        # Validate settings
        classes_selection_mode = self.local_settings.getSetting('Classes_Selection_Mode')
        classSetting = self.local_settings.getSetting('Selected_Classes')
        imported_file_setting = self.local_settings.getSetting('Json_Classes_File')
        if classes_selection_mode == 'text' and not classSetting.strip():
            raise IngestModuleException('No classes selected.')
        if classes_selection_mode == 'file':
            if imported_file_setting is None:
                raise IngestModuleException('No JSON file selected.')
            if not os.path.isfile(imported_file_setting):
                raise IngestModuleException('Selected JSON file not found.')
        
        # create custom artifact and attributes
        self.confidence_attr_type = self.createCustomAttributeType(self.CONFIDENCE_ATTR_TYPE_NAME, 'Best confidence')
        self.result_attr_type = self.createCustomAttributeType(self.RESULT_ATTR_TYPE_NAME, 'Image with results')
        self.class_attr_type = self.createCustomAttributeType(self.CLASS_ATTR_TYPE_NAME, 'Class')
        self.doi_art_type = self.createCustomArtifactType(self.DOI_ARTIFACT_TYPE_NAME, 'LabCIF DOI - Object Detected')
        
        self.context = context

    # Where the analysis is done.
    # The 'dataSource' object being passed in is of type org.sleuthkit.datamodel.Content.
    # 'progressBar' is of type org.sleuthkit.autopsy.ingest.DataSourceIngestModuleProgress
    def process(self, dataSource, progressBar):

        # we don't know how much work there is yet
        progressBar.switchToIndeterminate()

        # get files with supported MIMEType
        try:            
            fileManager = Case.getCurrentCase().getServices().getFileManager()
            files = fileManager.findFilesByMimeType(dataSource, self._supported_images_types)
        except TskCoreException:
            self.log(Level.SEVERE, 'Error getting files')
            return IngestModule.ProcessResult.ERROR

        # count the files
        num_files = len(files)
        if not num_files:
            message = "No images found: did you run the 'File Type Identification' module before running 'Detection of Objects in Images'?"
            self.log(Level.WARNING, message)
            self.notifyUser(IngestMessage.MessageType.WARNING, message)
            return IngestModule.ProcessResult.OK

        self.log(Level.INFO, 'Found ' + str(num_files) + ' files')

        # amount of work: copy each file + process each file
        progressBar.switchToDeterminate(num_files * 2)

        # create temp directory, if not exists
        self.temp_dir = self.createTempDir(dataSource.getName())
         # set results directory
        self.results_dir = os.path.join(Case.getCurrentCase().getModulesOutputDirAbsPath(), 
            DoiDataSourceIngestModuleFactory.moduleName, dataSource.getName(), 'results')

        ##### Copy the files to the temp directory     
        file_counter = 0
        for file in files:
            # Check if the user pressed cancel while we were busy
            if self.context.isJobCancelled():
                return IngestModule.ProcessResult.OK
            file_size = file.getSize()
            if file_size <= 0:
                self.log(Level.WARNING, 'File ' + file.getName() + ' seems corrupted (size not > 0)')
            elif file_size < self.MIN_FILE_SIZE:
                self.log(Level.WARNING, 'File ' + file.getName() + ' is too small (size < ' + str(self.MIN_FILE_SIZE) + ' bytes)')
            else:
                 # copy file
                ContentUtils.writeToFile(file, File(os.path.join(self.temp_dir, str(file.getId()) + '.' + file.getName())))
                
            # Update the progress bar
            file_counter += 1
            progressBar.progress('copying files to temporary directory', file_counter)

        if self.context.isJobCancelled():
            return IngestModule.ProcessResult.OK
        
        ##### Run detection for all images in temp directory
        try:
            self.runDetection(progressBar, file_counter)
        except Exception as e:
            self.log(Level.SEVERE, 'Error running doi.exe: ' + str(e))
            self.notifyUser(IngestMessage.MessageType.ERROR, 'Error running detection: '+ str(e))
            return IngestModule.ProcessResult.ERROR
        self.log(Level.INFO, 'Image object detection finished')

        ##### Handle results
        results_file_path = os.path.join(self.results_dir, 'results.json')
        with open(results_file_path) as json_file:
            results = json.load(json_file)
        results_count = 0
        for class_name, image_results_list in results.items():
            results_count += len(image_results_list)
            for image_result in image_results_list:
                filename = os.path.basename(image_result['image'])
                file_id = int(filename.split('.')[0])
                for file in files:
                    if file.getId() == file_id:
                        self.postToBlackboard(file, class_name, image_result['imageWithResults'], image_result['bestConfidence'])

        ##### Post a success message to the ingest messages in box
        message = IngestMessage.createMessage(IngestMessage.MessageType.DATA,
            DoiDataSourceIngestModuleFactory.moduleName, 
            "Processed %d image files: found %d results." % (file_counter, results_count))
        IngestServices.getInstance().postMessage(message)

        return IngestModule.ProcessResult.OK

    def createCustomAttributeType(self, attr_type_name, attr_desc):
        skCase = Case.getCurrentCase().getSleuthkitCase()
        try:
            skCase.addArtifactAttributeType(attr_type_name, BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, attr_desc)
        except:
            self.log(Level.INFO, 'Error creating attribute type: ' + attr_type_name)
        return skCase.getAttributeType(attr_type_name)

    def createCustomArtifactType(self, art_type_name, art_desc):
        skCase = Case.getCurrentCase().getSleuthkitCase()
        try:
            skCase.addBlackboardArtifactType(art_type_name, art_desc)
        except:
            self.log(Level.INFO, 'Error creating artifact type: ' + art_type_name)
        return skCase.getArtifactType(art_type_name)  

    def notifyUser(self, message_type, message):
        ingest_message = IngestMessage.createMessage(message_type,
            DoiDataSourceIngestModuleFactory.moduleName, message)
        IngestServices.getInstance().postMessage(ingest_message)
    
    def createTempDir(self, data_source_name):
        temp_dir = os.path.join(Case.getCurrentCase().getModulesOutputDirAbsPath(), 
            DoiDataSourceIngestModuleFactory.moduleName, data_source_name, 'original_files')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return temp_dir

    def generateArguments(self):
        classes_selection_mode = self.local_settings.getSetting('Classes_Selection_Mode')
        threshold = self.local_settings.getSetting('Selected_Threshold')
        config = self.local_settings.getSetting('Use_Configuration')        
        use_cpu = self.local_settings.getSetting('Use_CPU') == 'true'

        cmd_args = [
            self.path_to_exe,
            '-rd', self.results_dir,
            '--config', config,
            'detect', self.temp_dir,
            '-nrc',
            '--threshold', str(threshold)]

        if use_cpu:
            cmd_args.append('--nogpu')

        if classes_selection_mode == 'file':
            imported_file = self.local_settings.getSetting('Json_Classes_File')
            cmd_args.extend(['-clsf', imported_file])
        else:
            classSetting = self.local_settings.getSetting('Selected_Classes')
            selected_classes = classSetting.replace(' ','').split(',')
            cmd_args.append('-cls')
            cmd_args.extend(selected_classes)
        
        return cmd_args

    def runDetection(self, progressBar, number_of_files):
        cmd_args = self.generateArguments()
        self.log(Level.INFO, 'Selected arguments: ' + str(cmd_args))

        process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        processed_files_counter = 0
        #Poll process for new output until finished
        for line in iter(process.stdout.readline, ''):
            # update progress bar (each line is a processed image)
            processed_files_counter += 1
            progressBar.progress('detecting objects in images', number_of_files + processed_files_counter)
            if self.context.isJobCancelled():
                # terminate the process. process.terminate() won't work, it will terminate the cmd.exe but not doi.exe
                subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=process.pid))
                self.log(Level.WARNING, 'Subprocess terminated due to job cancelation')
                break

        stdout_data, stderr_data = process.communicate() # stdout_data will be empty (because of previous code: stdout.readline)
        exit_code = process.returncode
        if not self.context.isJobCancelled() and exit_code != 0:
            self.log(Level.SEVERE, 'Error in run detection: ' + stderr_data + '(return code: ' + str(exit_code) + ')')
            # get the message useful for user and raise excetion with it
            if 'error: ' in stderr_data:
                error_message = stderr_data.split('error: ')[1]
            else:
                error_message = 'Error running detection'
            raise Exception(error_message)

    def postToBlackboard(self, file, class_name, image_with_results, best_confidence):      
        # check if already exists an artifact for this file, with same object class
        doi_artifacts_list = file.getArtifacts(self.DOI_ARTIFACT_TYPE_NAME)
        for doi_artifact in doi_artifacts_list:
            attribute_list = doi_artifact.getAttributes()
            for attrib in attribute_list:
                if attrib.getAttributeTypeName() == self.CLASS_ATTR_TYPE_NAME and attrib.getValueString() == class_name:
                    self.log(Level.INFO, 'Artifact with same object class already exists for file ' + file.getName() + ', not making same artifact.')
                    return

        # Make an artifact on the blackboard.
        art = file.newArtifact(self.doi_art_type.getTypeID())
        # add attributes
        att_class = BlackboardAttribute(self.class_attr_type, 
            DoiDataSourceIngestModuleFactory.moduleName, class_name)
        att_comment = BlackboardAttribute(BlackboardAttribute.ATTRIBUTE_TYPE.TSK_COMMENT, 
            DoiDataSourceIngestModuleFactory.moduleName, 'Detection Of Objects in Images module detected ' + class_name + ' in this image')
        att_result_image = BlackboardAttribute(self.result_attr_type, 
            DoiDataSourceIngestModuleFactory.moduleName, image_with_results)
        att_best_confidence = BlackboardAttribute(self.confidence_attr_type, 
            DoiDataSourceIngestModuleFactory.moduleName, str(best_confidence))
        art.addAttributes([att_class, att_comment, att_result_image, att_best_confidence])

        blackboard = Case.getCurrentCase().getServices().getBlackboard() 
        try:
            # index the artifact for keyword search
            blackboard.indexArtifact(art)
        except Blackboard.BlackboardException as e:
            self.log(Level.SEVERE, "Error indexing artifact " + art.getDisplayName())


# Runnable class to avoid GUI lock
class DoRunnable(Runnable):
    def __init__(self, panelSettings, documentField):
        self.panelSettings = panelSettings
        self.documentField = documentField
    
    def run(self):
        self.panelSettings.changeText(self.documentField)


#-------------------------------------------------------------------------------
# Name: DL()
# Role: Implement a DocumentListener class to monitor text changes to a textfield
#-------------------------------------------------------------------------------
class DL( DocumentListener ) :

    def __init__(self, panelSettings, documentField):
        self.panelSettings = panelSettings
        self.documentField = documentField
    #---------------------------------------------------------------------------
    # Name: changedUpdate()
    # Role: DocumentListener event handler
    #---------------------------------------------------------------------------
    def changedUpdate( self, e ) :
        # postpones execution until Document lock is released.
        # https://alvinalexander.com/java/java-swingutilities-invoke-later-example-edt/
        SwingUtilities.invokeLater(DoRunnable(self.panelSettings, self.documentField))

    #---------------------------------------------------------------------------
    # Name: insertUpdate()
    # Role: DocumentListener event handler
    #---------------------------------------------------------------------------
    def insertUpdate( self, e ) :
        #self.panelSettings.changeText(self.documentField)
        SwingUtilities.invokeLater(DoRunnable(self.panelSettings, self.documentField))

    #---------------------------------------------------------------------------
    # Name: removeUpdate()
    # Role: DocumentListener event handler
    #---------------------------------------------------------------------------
    def removeUpdate( self, e ) :
        #self.panelSettings.changeText(self.documentField)
        SwingUtilities.invokeLater(DoRunnable(self.panelSettings, self.documentField))
		

# UI that is shown to user for each ingest job so they can configure the job.
class DoiDataSourceIngestModuleGUISettingsPanel(IngestModuleIngestJobSettingsPanel):
    # Note, we can't use a self.settings instance variable.
    # Rather, self.local_settings is used.
    # https://wiki.python.org/jython/UserGuide#javabean-properties
    # Jython Introspector generates a property - 'settings' on the basis
    # of getSettings() defined in this class. Since only getter function
    # is present, it creates a read-only 'settings' property. This auto-
    # generated read-only property overshadows the instance-variable -
    # 'settings'
    
    # We get passed in a previous version of the settings so that we can
    # prepopulate the UI
    def __init__(self, settings):
        self.local_settings = settings
        self.initComponents()
        self.customizeComponents()

    def changeText(self, documentField):
        if documentField == 'classes':
            self.local_settings.setSetting('Selected_Classes', self.textClasses.getText())

        if documentField == 'threshold':
            if len(self.textThreshold.getText()) > 0:
                threshold = self.textThreshold.getText()
                try:
                    parsedThreshold = float (threshold)
                    if parsedThreshold > 0.99 or parsedThreshold < 0:
                        parsedThreshold = 0.5
                        self.textThreshold.setText('0.5')
                    self.local_settings.setSetting('Selected_Threshold', str(parsedThreshold))
                except:
                    parsedThreshold = 0.5
                    self.textThreshold.setText('0.5')
                    self.local_settings.setSetting('Selected_Threshold', str(parsedThreshold))

    #---------------------------------------------------------------------------
    # Name: selection()
    # Role: ListSelectionListener event handler
    #---------------------------------------------------------------------------
    def selection( self, e ) :
        if e.getValueIsAdjusting() :
            si = e.getSource().getSelectedIndex()
            if si == 0:
                self.local_settings.setSetting('Use_Configuration', 'tiny')
            else:
                self.local_settings.setSetting('Use_Configuration', 'default')
            
    # Check the checkboxs to see what actions need to be taken
    def checkBoxEvent(self, event):
        if self.checkBoxForceCPU.isSelected():
            self.local_settings.setSetting('Use_CPU', 'true')
        else:
            self.local_settings.setSetting('Use_CPU', 'false')
           
    # When button to find file is clicked then open dialog to find the file and return it.       
    def onClickImport(self, e):
        chooseFile = JFileChooser()
        filter = FileNameExtensionFilter("json", ["json"])
        chooseFile.setFileFilter(filter)
        currentDirectory = self.local_settings.getSetting('User_Directory')
        if currentDirectory is not None and os.path.exists(currentDirectory):
            chooseFile.setCurrentDirectory(File(currentDirectory))

        ret = chooseFile.showDialog(self, "Select Json")

        if ret == JFileChooser.APPROVE_OPTION:
            file = chooseFile.getSelectedFile()
            canonical_file = file.getCanonicalPath()
            self.local_settings.setSetting('Json_Classes_File', canonical_file)
            self.selectedFileLabel.setText(os.path.basename(canonical_file))
            self.local_settings.setSetting('User_Directory', os.path.dirname(canonical_file))
        else:
            self.local_settings.setSetting('Json_Classes_File', None)
            self.selectedFileLabel.setText('(no file)')

    def onClickGetTemplate(self, e):
        chooseFile = JFileChooser()
        chooseFile.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
        currentDirectory = self.local_settings.getSetting('User_Directory')
        if currentDirectory is not None and os.path.exists(currentDirectory):
            chooseFile.setCurrentDirectory(File(currentDirectory))

        ret = chooseFile.showDialog(self, "Generate")

        if ret == JFileChooser.APPROVE_OPTION:
            directory = chooseFile.getSelectedFile().getAbsolutePath()
            self.local_settings.setSetting('User_Directory', directory)
            module_path = os.path.dirname(os.path.abspath(__file__))
            path_to_exe = os.path.join(module_path, 'doi.exe')
            if not os.path.exists(path_to_exe):
                raise IngestModuleException('Executable file not found!')
            cmd_args = [path_to_exe,
            '-rd', directory,
            '--config', self.local_settings.getSetting('Use_Configuration'),
            'classes']
            process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def radioBtnEvent(self, e):
        isImportSelected = self.radioBtnImport.isSelected()
        self.textClasses.setEditable(not isImportSelected)
        self.importButton.setEnabled(isImportSelected)
        self.local_settings.setSetting('Classes_Selection_Mode', 'file' if isImportSelected else 'text')

    # Create the initial data fields/layout in the UI
    def initComponents(self):
        self.setLayout(BoxLayout(self, BoxLayout.Y_AXIS))
        self.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        
        # main panel
        panelTop = JPanel()
        panelTop.setLayout(BoxLayout(panelTop, BoxLayout.Y_AXIS))
        labelWarning = JLabel("NOTE: Run first 'File Type Identification' module")
        panelTop.add(labelWarning)
        panelTop.add(JLabel(" "))
        labelTop = JLabel("<html><strong>DOI Settings</strong></html>")
        panelTop.add(labelTop)
        panelTop.add(JLabel(" "))

        # CPU/GPU option
        self.checkBoxForceCPU = JCheckBox("Use CPU instead of GPU (GPU is faster, but requires CUDA)", actionPerformed=self.checkBoxEvent)
        panelTop.add(self.checkBoxForceCPU)
        panelTop.add(JLabel(" "))

        # generate template
        panelGetTemplate = JPanel()
        panelGetTemplate.setLayout(BoxLayout(panelGetTemplate, BoxLayout.Y_AXIS))
        labelGetTemplate = JLabel("Generate JSON template with supported classes:")
        panelGetTemplate.add(labelGetTemplate)
        getTemplateButton = JButton("Generate JSON template", actionPerformed=self.onClickGetTemplate)
        panelGetTemplate.add(getTemplateButton)
        
        # import file
        panelImport = JPanel()
        panelImport.setLayout(BoxLayout(panelImport, BoxLayout.X_AXIS))
        panelImport.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        self.importButton = JButton("Import JSON", actionPerformed=self.onClickImport)
        panelImport.add(self.importButton)
        panelImport.add(JLabel(" "))
        self.selectedFileLabel = JLabel("")
        panelImport.add(self.selectedFileLabel)

        # panel for select classes in textbox
        panelClassesTextbox = JPanel()
        panelClassesTextbox.setLayout(BoxLayout(panelClassesTextbox, BoxLayout.Y_AXIS))
        panelImport.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        labelClasses = JLabel("List of classes to detect (separated by ','):")
        self.textClasses = JTextField()
        self.textClasses.getDocument().addDocumentListener( DL(self, 'classes') )
        self.textClasses.setMaximumSize(Dimension(400, 24))
        self.textClasses.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        panelClassesTextbox.add(labelClasses)
        panelClassesTextbox.add(self.textClasses)

        # radio button for panel import file
        panelRadioBtnImport = JPanel()
        panelRadioBtnImport.setLayout(BoxLayout(panelRadioBtnImport, BoxLayout.X_AXIS))
        panelRadioBtnImport.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        self.radioBtnImport = JRadioButton(actionPerformed=self.radioBtnEvent)
        panelRadioBtnImport.add(self.radioBtnImport)
        panelRadioBtnImport.add(panelImport)

        # radio button for panel to select classes in textbox
        panelRadioBtnSelectClasses = JPanel()
        panelRadioBtnSelectClasses.setLayout(BoxLayout(panelRadioBtnSelectClasses, BoxLayout.X_AXIS))
        panelRadioBtnSelectClasses.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        self.radioBtnSelectClasses = JRadioButton(actionPerformed=self.radioBtnEvent)
        panelRadioBtnSelectClasses.add(self.radioBtnSelectClasses)
        panelRadioBtnSelectClasses.add(panelClassesTextbox)

        # group radiobuttons
        panelGroupRadioBtns = JPanel()
        panelGroupRadioBtns.setLayout(BoxLayout(panelGroupRadioBtns, BoxLayout.Y_AXIS))
        buttonGroup = ButtonGroup()
        buttonGroup.add(self.radioBtnImport)
        buttonGroup.add(self.radioBtnSelectClasses)
        panelGroupRadioBtns.add(JLabel(" "))
        panelGroupRadioBtns.add(panelRadioBtnImport)
        panelGroupRadioBtns.add(JLabel(" "))
        panelGroupRadioBtns.add(panelRadioBtnSelectClasses)
        panelGroupRadioBtns.setBorder(BorderFactory.createTitledBorder("Specify classes to detect"))

        # threshold
        panelThreshold = JPanel()
        panelThreshold.setLayout(BoxLayout(panelThreshold, BoxLayout.X_AXIS))
        panelThreshold.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        labelThreshold = JLabel("Confidence threshold (0.1-0.99):")
        self.textThreshold = JTextField()
        self.textThreshold.getDocument().addDocumentListener(DL(self, 'threshold'))
        self.textThreshold.setMaximumSize(Dimension(30, 24))
        panelThreshold.add(labelThreshold)
        panelThreshold.add(JLabel(" "))
        panelThreshold.add(self.textThreshold)

        # config
        data = ['tiny (faster, but less accurate)', 'default']
        model = DefaultListModel()
        for word in data:
            model.addElement(word)
        self.config = JList(model,
            valueChanged=self.selection,
            selectionMode=ListSelectionModel.SINGLE_SELECTION)
        scrollPane = JScrollPane(self.config, preferredSize=(int(self.getSize().getWidth()), 50))
        scrollPane.setAlignmentX(JComponent.LEFT_ALIGNMENT)
        
        # add panels to main
        self.add(panelTop)
        self.add(panelGetTemplate)
        self.add(JLabel(" "))
        self.add(panelGroupRadioBtns)
        self.add(JLabel(" "))
        self.add(panelThreshold)
        self.add(JLabel(" "))
        self.add(JLabel("Configuration:"))
        self.add(scrollPane)

    # Custom load any data field and initialize the values
    def customizeComponents(self):
        # use CPU check box
        self.checkBoxForceCPU.setSelected(self.local_settings.getSetting('Use_CPU') == 'true')

        # classes radio button
        if self.local_settings.getSetting('Classes_Selection_Mode') == 'file':
            self.radioBtnImport.setSelected(True)
        else:
            self.radioBtnSelectClasses.setSelected(True)
            self.local_settings.setSetting('Classes_Selection_Mode', 'text')
        self.radioBtnEvent(None)

        # classes file
        selected_file = self.local_settings.getSetting('Json_Classes_File')
        if selected_file is not None:
            if os.path.isfile(selected_file):
                self.selectedFileLabel.setText(os.path.basename(selected_file))
            else:
                self.local_settings.setSetting('Json_Classes_File', None)
                self.selectedFileLabel.setText('(no file)')
        else:
            self.selectedFileLabel.setText('(no file)')

        # classes text box
        self.textClasses.setText(self.local_settings.getSetting('Selected_Classes'))
        self.changeText('classes')
        
        # threshold
        if not self.local_settings.getSetting('Selected_Threshold'):
            self.local_settings.setSetting('Selected_Threshold', '0.5')
        self.textThreshold.setText(self.local_settings.getSetting('Selected_Threshold'))
        self.changeText('threshold')

        # configuration
        if self.local_settings.getSetting('Use_Configuration') == 'tiny':
            self.config.setSelectedIndex(0)
        else:
            self.config.setSelectedIndex(1)
            self.local_settings.setSetting('Use_Configuration', 'default')

    # Return the settings used
    def getSettings(self):
        return self.local_settings