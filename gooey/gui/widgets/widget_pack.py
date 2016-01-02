from functools import partial
from gooey.gui.lang import i18n
from gooey.gui.util.filedrop import FileDrop
from gooey.gui.util.quoting import quote

__author__ = 'Chris'

from abc import ABCMeta, abstractmethod

import os
import wx
import wx.lib.agw.multidirdialog as MDD

from gooey.gui.widgets.calender_dialog import CalendarDlg


class WidgetPack(object):
  """
  Interface specifying the contract to which
  all `WidgetPack`s will adhere
  """
  __metaclass__ = ABCMeta

  @abstractmethod
  def build(self, parent, data):
    pass

  def onResize(self, evt):
    pass

  @staticmethod
  def get_command(data):
    return ''

  @staticmethod
  def disable_quoting(data):
    nargs = data.get('nargs', None)
    if not nargs:
      return False
    return nargs not in (1, '?')


class BaseChooser(WidgetPack):
  def __init__(self):
    self.button_text = i18n._('browse')
    self.option_string = None
    self.parent = None
    self.widget = None
    self.button = None

  def build(self, parent, data):
    self.parent = parent
    self.option_string = self.get_command(data)
    self.widget = wx.TextCtrl(self.parent)
    self.widget.AppendText(safe_default(data, ''))
    self.widget.SetMinSize((0, -1))
    dt = FileDrop(self.widget)
    self.widget.SetDropTarget(dt)
    self.button = wx.Button(self.parent, label=self.button_text, size=(73, 23))

    widget_sizer = wx.BoxSizer(wx.HORIZONTAL)
    widget_sizer.Add(self.widget, 1, wx.EXPAND)
    widget_sizer.AddSpacer(10)
    widget_sizer.Add(self.button, 0, wx.ALIGN_CENTER_VERTICAL)

    parent.Bind(wx.EVT_BUTTON, self.onButton, self.button)
    return widget_sizer

  def get_value(self):
    return self.widget.GetValue()

  # def getValue(self):
  #   value = self.widget.GetValue()
  #   if self.option_string and value:
  #     return '{0} {1}'.format(self.option_string, quote(value))
  #   else:
  #     return quote(value) if value else ''
  #
  # def onButton(self, evt):
  #   raise NotImplementedError

  def __repr__(self):
    return self.__class__.__name__


class BaseFileChooser(BaseChooser):
  dialog = None
  def __init__(self):
    BaseChooser.__init__(self)

  def onButton(self, evt):
    dlg = self.dialog(self.parent)
    result = (self.get_path(dlg)
              if dlg.ShowModal() == wx.ID_OK
              else None)
    if result:
      self.widget.SetValue(result)

  def get_path(self, dlg):
    return dlg.GetPath()


class BaseMultiFileChooser(BaseFileChooser):
  def __init__(self, dialog):
    BaseFileChooser.__init__(self)
    self.dialog = dialog

  # def getValue(self):
  #   value = ' '.join(quote(x) for x in self.widget.GetValue().split(os.pathsep) if x)
  #   if self.option_string and value:
  #     return '{} {}'.format(self.option_string, value)
  #   return value or ''

  def get_path(self, dlg):
    return os.pathsep.join(dlg.GetPaths())

class MultiFileSaverPayload(BaseMultiFileChooser):
  def __init__(self, *args, **kwargs):
    BaseMultiFileChooser.__init__(self, build_dialog(wx.FD_MULTIPLE, False))

class MultiDirChooserPayload(BaseMultiFileChooser):
  class MyMultiDirChooser(MDD.MultiDirDialog):
    def __init__(self, *args, **kwargs):
      kwargs.update({
        'title': "Select Directories",
        'defaultPath': os.getcwd(),
        'agwStyle': MDD.DD_MULTIPLE|MDD.DD_DIR_MUST_EXIST
      })
      MDD.MultiDirDialog.__init__(self, *args, **kwargs)

    def GetPaths(self):
      return self.dirCtrl.GetPaths()

  def __init__(self, *args, **kwargs):
    BaseMultiFileChooser.__init__(self, MultiDirChooserPayload.MyMultiDirChooser)



class TextInputPayload(WidgetPack):
  def __init__(self, no_quoting=False):
    self.widget = None
    self.option_string = None
    self.no_quoting = no_quoting

  def build(self, parent, data):
    self.option_string = self.get_command(data)
    if self.disable_quoting(data):
      self.no_quoting = True
    self.widget = wx.TextCtrl(parent)
    dt = FileDrop(self.widget)
    self.widget.SetDropTarget(dt)
    self.widget.SetMinSize((0, -1))
    self.widget.SetDoubleBuffered(True)
    self.widget.AppendText(safe_default(data, ''))
    return self.widget

  def get_value(self):
    return self.widget.GetValue()

  # def getValue(self):
  #   if self.no_quoting:
  #     _quote = lambda value: value
  #   else:
  #     _quote = quote
  #   value = self.widget.GetValue()
  #   if value and self.option_string:
  #     return '{} {}'.format(self.option_string, _quote(value))
  #   else:
  #     return _quote(value) if value else ''
  #
  # def _SetValue(self, text):
  #   # used for testing
  #   self.widget.SetLabelText(text)


class DropdownPayload(WidgetPack):
  default_value = 'Select Option'

  def __init__(self, no_quoting=False):
    self.widget = None
    self.option_string = None
    self.no_quoting = no_quoting

  def build(self, parent, data):
    self.option_string = self.get_command(data)
    if self.disable_quoting(data):
      self.no_quoting = True
    self.widget = wx.ComboBox(
      parent=parent,
      id=-1,
      value=safe_default(data, self.default_value),
      choices=[],
      style=wx.CB_DROPDOWN
    )
    return self.widget

  def get_value(self):
    return self.widget.GetValue()

  # def getValue(self):
  #   if self.no_quoting:
  #     _quote = lambda value: value
  #   else:
  #     _quote = quote
  #   value = self.widget.GetValue()
  #   if value == self.default_value:
  #     return ''
  #   elif value and self.option_string:
  #     return '{} {}'.format(self.option_string, _quote(value))
  #   else:
  #     return _quote(value) if value else ''

  def _SetValue(self, text):
    # used for testing
    self.widget.SetLabelText(text)


class CounterPayload(WidgetPack):
  def __init__(self):
    self.option_string = None
    self.widget = None

  def build(self, parent, data):
    self.option_string = self.get_command(data)
    self.widget = wx.ComboBox(
      parent=parent,
      id=-1,
      value=safe_default(data, ''),
      choices=map(str, range(1, 11)),
      style=wx.CB_DROPDOWN
    )
    return self.widget

  def get_value(self):
    return self.widget.GetValue()

  # def getValue(self):
  #   '''
  #   Returns
  #     str(option_string * DropDown Value)
  #     e.g.
  #     -vvvvv
  #   '''
  #   return self.widget.GetValue()
    # if not str(dropdown_value).isdigit():
    #   return ''
    # arg = str(self.option_string).replace('-', '')
    # repeated_args = arg * int(dropdown_value)
    # return '-' + repeated_args

  # def getValue(self):
  #   '''
  #   Returns
  #     str(option_string * DropDown Value)
  #     e.g.
  #     -vvvvv
  #   '''
  #   dropdown_value = self.widget.GetValue()
  #   if not str(dropdown_value).isdigit():
  #     return ''
  #   arg = str(self.option_string).replace('-', '')
  #   repeated_args = arg * int(dropdown_value)
  #   return '-' + repeated_args

class DirDialog(wx.DirDialog):
  def __init__(self, parent, *args, **kwargs):
    wx.DirDialog.__init__(self, parent, 'Select Directory', style=wx.DD_DEFAULT_STYLE)

def safe_default(data, default):
  # str(None) is 'None'!? Whaaaaat...?
  # return str(data['default']) if data['default'] else default
  return ''

def build_dialog(style, exist_constraint=True, **kwargs):
  if exist_constraint:
    return lambda panel: wx.FileDialog(panel, style=style | wx.FD_FILE_MUST_EXIST, **kwargs)
  else:
    return lambda panel: wx.FileDialog(panel, style=style, **kwargs)


def build_subclass(subclass, dialog):
  return type(subclass, (BaseFileChooser,), {'dialog': dialog})

FileSaverPayload   = build_subclass('FileSaverPayload', staticmethod(build_dialog(wx.FD_SAVE, False, defaultFile="Enter Filename")))
FileChooserPayload = build_subclass('FileChooserPayload', staticmethod(build_dialog(wx.FD_OPEN)))
DirChooserPayload  = build_subclass('DirChooserPayload', DirDialog)
DateChooserPayload = build_subclass('DateChooserPayload', CalendarDlg)
