import os
import api
import config
import globalPluginHandler
from scriptHandler import script
import gui
import globalVars
from gui.message import displayDialogAsModal
import wx
import ui
import re
import tones

fname_re = re.compile(r'[<>:"/\\|?*]')
def escape_filename(name):
	# Windows doesn't like trailing .
	name = re.sub(r'\.$', '_', name)
	# Remove leading and trailing whitespace
	name = name.strip()
	return fname_re.sub('_', name)

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(Panel)
		confspec = {
			'path': 'string(default="")',
		}
		config.conf.spec['addFavorites'] = confspec

	@script(
	description=_("Add favorite"),
	gesture="kb:NVDA+ALT+A")
	@gui.blockAction.when(gui.blockAction.Context.MODAL_DIALOG_OPEN)
	def script_addFavorite(self, gesture):
		obj = api.getNavigatorObject()
		t = obj.treeInterceptor
		if t is None:
			ui.message(_("Not in a browse mode document"))
			return
		if 'addFavorites' not in config.conf or config.conf['addFavorites']['path'] == '':
			ui.message(_("Add favorites path is not set."))
			return
		root = t.rootNVDAObject
		title = root.name
		url = t.documentURL
		wx.CallAfter(self.add, title, url)

	def add(self, title, url):
		gui.mainFrame.prePopup()
		dlg = AddFavoriteDialog(title, url)
		if displayDialogAsModal(dlg) != wx.ID_OK:
			dlg.Destroy()
			return
		gui.mainFrame.postPopup()
		title = dlg.title_edit.GetValue()
		url = dlg.url_edit.GetValue()
		dlg.Destroy()
		path = config.conf['addFavorites']['path']
		filename = os.path.join(path, escape_filename(title))
		if len(filename) > 255:
			filename = filename[:255]
		filename += '.url'
		data = f"""[InternetShortcut]
		URL={url}
		"""
		with open(filename, "w") as fp:
			fp.write(data)
		tones.beep(800, 100)

class AddFavoriteDialog(wx.Dialog):
	def __init__(self, title, url):
		super().__init__(gui.mainFrame, wx.ID_ANY, "Add favorite")
		self.title = title
		self.url = url
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, wx.VERTICAL)
		self.title_edit = sHelper.addLabeledControl(_("&Title:"), wx.TextCtrl)
		self.url_edit = sHelper.addLabeledControl(_("&URL:"), wx.TextCtrl)
		self.title_edit.SetValue(self.title)
		self.url_edit.SetValue(self.url)
		mainSizer.Add(sHelper.sizer, border=10, flag=wx.ALL)
		mainSizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL))
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.title_edit.SetFocus()
		self.Bind(wx.EVT_BUTTON, self.onOk, id=wx.ID_OK)

	def onOk(self, evt):
		title = self.title_edit.GetValue()
		url = self.url_edit.GetValue()
		if not title or not url:
			gui.messageBox(_("Title and URL must be set."), _("Error"), wx.OK | wx.ICON_ERROR)
			return
		evt.Skip()

class Panel(gui.settingsDialogs.SettingsPanel):
	title = _("Add favorites")
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.path = None

	def makeSettings(self, settingsSizer):
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		groupSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=_("Directory"))
		groupHelper = helper.addItem(gui.guiHelper.BoxSizerHelper(self, sizer=groupSizer))
		groupBox = groupSizer.GetStaticBox()
		self.path_helper = helper.addItem(gui.guiHelper.PathSelectionHelper(groupBox, _("Select folder"), _("Select favorites folder")))
		if config.conf['addFavorites']['path']:
			self.path_helper.pathControl.SetValue(config.conf['addFavorites']['path'])

	def onSave(self):
		if self.path_helper.pathControl.GetValue() != '':
			config.conf['addFavorites']['path'] = self.path_helper.pathControl.GetValue()

if globalVars.appArgs.secure:
	class GlobalPlugin:
		pass
