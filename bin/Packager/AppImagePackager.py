from Packager.CollectionPackagerBase import *

class AppImagePackager(CollectionPackagerBase):
    @InitGuard.init_once
    def __init__( self, whitelists=None, blacklists=None):
        CollectionPackagerBase.__init__(self, whitelists, blacklists)

    def setDefaults(self, defines: {str:str}) -> {str:str}:
        defines = super().setDefaults(defines)
        defines["setupname"] = f"{defines['setupname']}.AppImage"
        return defines

    def createPackage( self ):
        """ create a package """
        CraftCore.log.debug("packaging using the AppImagePackager")

        archiveDir = Path(self.archiveDir())
        defines = self.setDefaults(self.defines)
        if not self.internalCreatePackage(defines, packageSymbols=False):
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
        env = {"ARCH": "x86_64", "LD_LIBRARY_PATH": f"{archiveDir}/usr/lib:{archiveDir}/usr/lib/x86_64-linux-gnu"}
        if OsUtils.detectDocker():
            env["APPIMAGE_EXTRACT_AND_RUN"] = "1"
        env["OUTPUT"] = defines["setupname"]
        env["VERSION"] = defines["version"]

        # create symlinks, because the libexec dir is not correctly found in the AppImages
        if (archiveDir / "usr/lib/libexec/kf5/kioslave5").exists():
            utils.system(["ln", "-s", archiveDir / "usr/lib/libexec/kf5/kioslave5", archiveDir/"usr/bin/"], cwd=self.packageDestinationDir())
            utils.system(["ln", "-s", archiveDir / "usr/lib/libexec/kf5/kioexec", archiveDir/"usr/bin/"], cwd=self.packageDestinationDir())

        with utils.ScopedEnv(env):
            args = ["--appdir", self.archiveDir(), "--plugin=qt", "--output=appimage", "--desktop-file", desktopFiles[0]]
            if CraftCore.debug.verbose() > 0:
                args += ["-v0"]
            return utils.system(["linuxdeploy-x86_64.AppImage"] + args, cwd=self.packageDestinationDir())
