#
# copyright (c) 2009 Ralf Habacker <ralf.habacker@freenet.de>
#
# Packager base

from EmergeBase import *

class PackagerBase(EmergeBase):
    """ provides a generic interface for packagers and implements basic package creating stuff """
    def __init__(self):
        EmergeBase.__init__(self)
        self.whitelist_file = None
        self.blacklist_file = None
        self.defines = {}
        self.ignoredPackages = []

    def preArchive(self):
        utils.abstract()

    def archiveDir(self):
        if self.package.endswith( "-package" ):
            return self.imageDir() # compat behavior

        return os.path.join( self.buildRoot(), "archive" )

    def getPackageVersion(self):
        """ return version information for the currently used package"""
        if self.subinfo.options.package.version != None:
            pkgVersion = self.subinfo.options.package.version
        else:
            versionFile = os.path.join(self.buildDir(),'emerge-package-version')
            if os.path.exists(versionFile):
                with open( versionFile, "r" ) as f:
                    pkgVersion = f.read()
            elif self.version == "all": 
                if self.subinfo.buildTarget == "gitHEAD":
                    pkgVersion = str( datetime.date.today() ).replace('-', '')  + '-' + self.source.sourceVersion()
                elif self.subinfo.buildTarget == "svnHEAD":
                    pkgVersion = str( datetime.date.today() ).replace('-', '')  + '-r' + self.source.sourceVersion()
                elif self.subinfo.buildTarget == "HEAD":
                    pkgVersion = str( datetime.date.today() ).replace('-', '')  + '-' + self.subinfo.buildTarget
                else:
                    pkgVersion = self.subinfo.buildTarget
            elif self.subinfo.buildTarget == "gitHEAD" or self.subinfo.buildTarget == "svnHEAD":
                pkgVersion = str( datetime.date.today() ).replace('-', '')
            else:
                pkgVersion = self.subinfo.buildTarget

        pkgNotesVersion = pkgVersion

        if ("General","EMERGE_PKGPATCHLVL") in emergeSettings:
            pkgVersion += "-" + emergeSettings.get("General","EMERGE_PKGPATCHLVL")

        return [pkgVersion, pkgNotesVersion]

    #""" create a package """
    def createPackage(self):
        utils.abstract()
