from Packager.CollectionPackagerBase import *

class AppImagePackager(CollectionPackagerBase):
    @InitGuard.init_once
    def __init__( self, whitelists=None, blacklists=None):
        CollectionPackagerBase.__init__(self, whitelists, blacklists)

    def setDefaults(self, defines: {str:str}) -> {str:str}:
        defines = super().setDefaults(defines)
        defines["setupname"] = f"{defines['setupname']}.AppImage"
        defines.setdefault("runenv",[
            # XDG_DATA_DIRS: to make QStandardPaths::GenericDataLocation look in the Appimage paths too.
            # Eg. necessary to make switching languages for KDE (with KConfigWidgets) applications work.
            'XDG_DATA_DIRS=$this_dir/usr/share/:$XDG_DATA_DIRS',
            'QT_PLUGIN_PATH=$this_dir/usr/plugins/',
            'PATH=$this_dir/usr/bin:$this_dir/usr/lib:$PATH'])
        return defines

    def createPackage( self ):
        """ create a package """
        CraftCore.log.debug("packaging using the AppImagePackager")

        archiveDir = Path(self.archiveDir())
        defines = self.setDefaults(self.defines)
        if not self.internalCreatePackage(defines, packageSymbols=True, seperateSymbolFiles=True):
            return False
        if not utils.mergeTree(archiveDir, archiveDir / "usr"):
            return False
        etc = archiveDir / "usr/etc"
        if etc.exists():
            if not utils.moveFile(etc, archiveDir / "etc"):
                return False
        if "runenv" in defines:
            if not utils.createDir(archiveDir / "apprun-hooks"):
                return False
            with (archiveDir / "apprun-hooks/craft-reunenv-hook.sh").open("wt") as hook:
                hook.write("# generated by craft based on the runenv define\n\n")
                hook.writelines([f"export {x}\n" for x in defines["runenv"]])
        if not utils.createDir(self.packageDestinationDir()):
            return False
        desktopFiles = glob.glob(f"{archiveDir}/usr/share/applications/*{defines['appname']}.desktop")
        if len(desktopFiles) != 1:
            CraftCore.log.error("Failed to find the .desktop file")
            return False
        env = {
            "ARCH": "x86_64",
            "LD_LIBRARY_PATH": f"{archiveDir}/usr/lib:{archiveDir}/usr/lib/x86_64-linux-gnu",
            "OUTPUT": defines["setupname"],
            "VERSION": defines["version"],
            "NO_STRIP": "1" # our binaries are already stripped
        }
        if OsUtils.detectDocker():
            env["APPIMAGE_EXTRACT_AND_RUN"] = "1"
        with utils.ScopedEnv(env):
            args = ["--appdir", self.archiveDir(), "--plugin=qt", "--output=appimage", "--desktop-file", desktopFiles[0]]
            if CraftCore.debug.verbose() > 0:
                args += ["-v0"]
            return utils.system(["linuxdeploy-x86_64.AppImage"] + args, cwd=self.packageDestinationDir())
