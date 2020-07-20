import os
from java.lang import System
from java.util.logging import Level
import java.nio.file.Paths
from org.sleuthkit.datamodel import TskData
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.report import GeneralReportModuleAdapter
from org.sleuthkit.autopsy.report.ReportProgressPanel import ReportStatus
from org.sleuthkit.autopsy.casemodule.services import FileManager
from org.sleuthkit.autopsy.coreutils import PlatformUtil
import org.sleuthkit.datamodel.BlackboardArtifact
import org.sleuthkit.datamodel.BlackboardAttribute
import org.sleuthkit.autopsy.casemodule.services.Blackboard
import org.sleuthkit.autopsy.casemodule.services.FileManager
from org.sleuthkit.autopsy.ingest import IngestServices
import jarray
import inspect

import html_writer
import js_writer
import file_writer

CONFIDENCE_ATTR_TYPE_NAME = 'DOI_BEST_CONFIDENCE'
DOI_ARTIFACT_TYPE_NAME = 'DOI_OBJECT_DETECTED'
RESULT_ATTR_TYPE_NAME = 'DOI_IMAGE_RESULT'
CLASS_ATTR_TYPE_NAME = 'DOI_CLASS'

class DoiReportModule(GeneralReportModuleAdapter):

    services = IngestServices.getInstance()
    moduleName = "LabCIF DOI Report"

    _logger = Logger.getLogger(moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__,
                          inspect.stack()[1][3], msg)

    def getName(self):
        return self.moduleName

    def getDescription(self):
        return "Report regarding Detection of Objects in Images"

    def getRelativeFilePath(self):
        return "LabCIF DOI - " + Case.getCurrentCase().getName() + ".html"

    def generateReport(self, baseReportDir, progressBar):
        
        # open output file
        fileName = os.path.join(baseReportDir, self.getRelativeFilePath())
        report = open(fileName, 'w')
        
        js_file_name = os.path.join(baseReportDir, "doi_report_data.js")
        js_report = open(js_file_name, 'w')

        sleuthkitCase = Case.getCurrentCase().getSleuthkitCase()
        fileManager = Case.getCurrentCase().getServices().getFileManager()

        base_query = "JOIN blackboard_artifact_types AS types ON blackboard_artifacts.artifact_type_id = types.artifact_type_id WHERE types.type_name LIKE "
        art_list_images = sleuthkitCase.getMatchingArtifacts(base_query + "'" + DOI_ARTIFACT_TYPE_NAME + "'")
        att_result = sleuthkitCase.getAttributeType(RESULT_ATTR_TYPE_NAME)
        class_result = sleuthkitCase.getAttributeType(CLASS_ATTR_TYPE_NAME)
        confidence_result = sleuthkitCase.getAttributeType(CONFIDENCE_ATTR_TYPE_NAME)

        report.write(html_writer.insert_prefix_html())
        js_report.write(js_writer.insert_prefix_js())

        # Setup the progress bar
        progressBar.setIndeterminate(False)
        progressBar.setMaximumProgress(len(art_list_images))
        progressBar.start()

        for art_item in art_list_images:
            item = art_item.getAttribute(att_result).getDisplayString()
            if not item:
                # DOI could not create image with results. Therefore, ignore this artifact.
                continue
            item_class = art_item.getAttribute(class_result).getDisplayString()
            item_confidence = art_item.getAttribute(confidence_result).getDisplayString()
            item_result_file = file_writer.copy_to_results_folder(baseReportDir, item)
            item_id = int(item.split('/')[-1].split('.')[0])
            file_name_with_extension = file_writer.get_file_with_extension(item)
            
            original_file_name_part = file_name_with_extension.split('.')[1]
            matched_files = fileManager.findFiles("%" + original_file_name_part + "%")
            if not matched_files:
                self.log(Level.SEVERE, 'File not found with name LIKE ' + original_file_name_part)
                progressBar.complete(ReportStatus.ERROR)
                return
            try:
                file = next(x for x in matched_files if x.getId() == item_id)
            except StopIteration:
                self.log(Level.SEVERE, 'File with id ' + str(item_id) + ' not found for name LIKE ' + original_file_name_part)
                progressBar.complete(ReportStatus.ERROR)
                return
            original_file_path = file.getUniquePath()
            file_size = round(float(file.getSize())/1024, 2)
            original_file_name = file_writer.get_file_original_with_extension(original_file_path)
            temp_dir = os.path.join(Case.getCurrentCase().getModulesOutputDirAbsPath(), 'Detection of Objects in Images', file.getDataSource().getName(), 'original_files')
            item_original_path = os.path.join(temp_dir, file_name_with_extension)
            item_original_file = file_writer.copy_to_original_folder(baseReportDir, item_original_path)
            
            js_string = js_writer.insert_object_js(item_result_file, item_original_file, original_file_name, original_file_path.replace("\\", "/"), item_class, file_size, item_confidence)
            js_report.write(str(js_string))
            progressBar.increment()

        report.write(html_writer.insert_suffix_html())
        js_report.write(js_writer.insert_suffix_js())

        report.close()
        js_report.close()

        # Add the report to the Case, so it is shown in the tree
        Case.getCurrentCase().addReport(fileName, self.moduleName, "Labcif@DOI Html report")
        Case.getCurrentCase().addReport(js_file_name, self.moduleName + "_js", "Labcif@DOI Javascript dataset")

        progressBar.complete(ReportStatus.COMPLETE)
