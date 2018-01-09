# -*- coding: utf8 -*-
################################################################################
#                                                                              #
#          FCINK                                                               #
#                                                                              #
#          Verze 0.3                                                           #
#                                                                              #
#   Program pro zobrazování grafů funkcí a jejich export.                      #
#   Kompletně třídová verze.                                                   #
#                                                                              #
#   Seznam obsažených tříd:                                                    #
#                                                                              #
#   BaseClass        - kořen všech tříd, definuje základní chování.            #
#    Processor        - procedurální třída propojující rozhraní s jádrem.      #
#    ComputingClass   - kořen tříd výpočtů a zpracování dat.                   #
#     Evaluator        - zpracovává mat. výrazy pro počítač a vyhodnocuje je.  #
#     SequenceCreator  - vytváří z dat posloupnosti pro zobrazení grafu.       #
#    OutputClass      - kořen tříd tvořících výstup.                           #
#     GUInterface      - /tk.Tk (základní aplikce Tkinteru).                   #
#     MainWindow       - třída hlavního okna (/tk.Frame).                      #
#     Plotter          - třída kreslicího plátna (grafy, /tk.Canvas).          #
#     ControlPanel     - třída seznamu funkcí a ovládacího panelu (/tk.Frame). #
#     MainMenu         - třída uspořádávání menu (/tk.Frame).                  #
#     StatusBar        - třída statusbaru (/tk.Label).                         #
#    SupportClass     - kořen tříd podpůrné práce (logy ap.)                   #
#     FileWorkClass    - kořen tříd pro práci se soubory.                      #
#      Config           - správce konfigurace a nastavení.                     #
#      Logger           - záznamník.                                           #
#   ErrorHandler      - obsluha výjimek.                                       #
#                                                                              #
#   Autor: Jan Šimbera - Prófa. All rights reserved.                           #
#                                                                              #
#   Seznam úprav:                                                              #
#                                                                              #
#   23.01.2009 - vytvoření dokumentace a základní struktury programu           #
#   24.01.2009 - práce na mřížce v Plotteru, dokončení matematických tříd      #
#   25.01.2009 - vytvoření StatusBaru, Menu, FileWorkClass etc. (z BrigManu)   #
#   07.02.2009 - dodělání Menu, optimalizace parametrů plotteru a mřížky       #
#   08.02.2009 - pokračování práce na Plotteru                                 #
#   26.05.2009 - obnova, přepracování modelu funkcí                            #
#   27.05.2009 - osekání na funkční součásti (core, osekání selectů)           #
#   31.05.2009 - práce na zoomu, úklid Plotteru (uspořádání metod)             #
#   01.11.2009 ->                                                              #
#   08.11.2009 - různé práce s mřížkou (scroll, úprava počítacího systému)     #
#   11.11.2009 - ladění, pokrok v editaci funkcí                               #
#   12.11.2009 - měřítko x v násobcích pí                                      #
#   27.11.2009 - celkový refaktoring (PlotComputer)                            #
#   12.02.2010 - pokračování refaktoringu                                      #
#   13.02.2010 ->                                                              #
#   02.03.2010 - refaktoring ukončen, plánování dalších vylepšení              #
#   09.03.2010 - začátek implementace ukládání do souborů                      #
#   10.03.2010 - ladění souborových operací                                    #
#                                                                              #
################################################################################

# TODOS: dodělat interface pro new/save/load
#        remap chybových hlášek
#        parametrické systémy funkcí - doladit
#        manuální změna xcountu
#        nový parser (PyParsing)
#        přidat podporu jiných zápisů funkcí (parser + definice)
#        podpora násobků pí v zobrazovači (2pi, kpi)
#        lepší sázení vzorců funkcí
#        scroll-lines i na major-grid
#        zaměřovací křížek
#        inverze funkce, derivace... ?
#        builtin kalkulačka -> jednoduchý matematický soft
#        ověřování výrazů (i za běhu zadávání)
#        lepší vyřešení parametriky (volitelná, k jako k in Z pro kpi)
#        analytické nástroje (tečna v bodě...)
#        nefunkce (rovnice pro x a y - kuželosečky...)

# importy
# import pdb
import sys, os, re, math
import tkinter as tk
import tkinter.filedialog as tkfdia
import tkinter.colorchooser as tkcolc
sys.path.append(os.path.join('..', 'lib'))
import base3 as base
from base3 import Date, String
import ioc, mathfx
log = None

DATAF_EXT = 'fxml'

# výjimky
class FunctionError(RuntimeError):
 pass

class BaseClass:
 name = 'BASE'
 
 def log(self, text):
  if log:
   log.logNamed(self.name, text)

# The Boss - main run frame
class Processor(BaseClass):
 name = 'MAIN'
 def __init__(self):
  self.cleaned = False
 
 def getFilePath(self):
  return self.filePath
 
 def setFilePath(self, filePath):
  self.filePath = filePath
  win.setTitle(self.getFileName())
   
 def getFileName(self):
  return self.filePath.split(os.sep)[-1]
  
 def getDefaultFileName(self):
  return self.defFileName
  
 def run(self):
  try:
   try:
    self.init()
    self.main()
   except (SystemExit, KeyboardInterrupt):
    raise
   except Exception as error:
    if errh: errh.handleMainError(error)
    else: raise
  finally:
   try:
    if not self.cleaned:
     self.cleanup()
   except:
    pass
 
 def init(self):
  global conf, log, win, errh, fman, comp, mgr
  errh = ErrorHandler()
  conf = Config()
  log = Logger()
  self.log('Starting')
  self.initFileMgr()
  self.filePath = os.path.join(conf.get('path', 'data'), self.getDefaultFileName())
  errh.stdReset()
  fman = FunctionManager()
  comp = PlotComputer()
  mgr = Manager()
  win = MainWindow(title=conf.get('out', 'window-title').format(self.getFileName()))
  win.init()
 
 def main(self):
  win.display()
  mgr.start()
  if len(sys.argv) > 1:
   for expr in sys.argv[1:]:
    mgr.createFunction(expr)
  win.mainloop()
 
 def initFileMgr(self):
  self.defFileName = conf.get('out', 'default-filename') + '.' + DATAF_EXT
 
 def cleanup(self):
  self.log('Exitting')
 
 def exit(self):
  sys.exit(0)
 
 

class ComputingClass(BaseClass):
 pass

# Trida spravce funkci.
class FunctionManager(ComputingClass):
 def __init__(self):
  self.functionId = 100
  self.resetFunctionOrds()
  self.functions = {}
  self.selected = None
 
 def createFunction(self, expr):
  fid = self.functionId
  self.functions[fid] = Function(fid, expr, number=self.functionOrd)
  self.countFunction(fid)
  self.functionId += 1
  self.functionOrd += 1
  return fid
 
 def editFunction(self, fid, expr):
  self.functions[fid].edit(expr)
  self.countFunction(fid)
 
 def loadFunction(self, fid, number, exprSrc, exprFin):
  self.functions[fid] = Function(fid, exprSrc, exprFin=exprFin, number=number)
  if fid >= self.functionId:
   self.functionId = fid + 1
  if number >= self.functionOrd:
   self.functionOrd = number + 1
  self.countFunction(fid)
 
 def resetFunctionOrds(self):
  self.functionOrd = 1
 
 def selectFunction(self, fid):
  self.unselectFunction(self.selected)
  self.thickerFunction(fid)
  self.selected = fid

 def unselectFunction(self, fid=None):
  fid = self.verifyFID(fid)
  if fid is not None:
   self.thinnerFunction(fid)
   self.selected = None

 def deleteFunction(self, fid=None):
  fid = self.verifyFID(fid)
  if fid == self.selected:
   self.selected = None
  if fid is not None:
   del self.functions[fid]

 def thickerFunction(self, fid):
  self.getFunction(fid).setLineWidth(conf.get('gridpar', 'highlight-function-linewidth'))
 
 def thinnerFunction(self, fid):
  self.getFunction(fid).setLineWidth(conf.get('gridpar', 'normal-function-linewidth'))
 
 def changeFuncColor(self, color, fid=None):
  if fid is None:
   fid = self.getSelectedFID()
  self.getFunction(fid).setColor(color)
 
 def countFunctions(self):
  for func in self.functions.values():
   func.count()
   
 def countFunction(self, fid):
  self.getFunction(fid).count()

 def getFunction(self, fid):
  try:
   return self.functions[fid]
  except IndexError:
   if self.selected:
    return self.functions[self.selected]
   else:
    raise IndexError('invalid internal function ID provided')
 
 def getSelectedFID(self):
  return self.selected
 
 def getExprEdit(self, fid):
  if self.selected:
   return self.functions[fid].getExpr()[4:]
  else:
   return ''
 
 def verifyFID(self, fid=None):
  if fid is None and self.selected is not None:
   return self.selected
  else:
   return fid

 def getFunctionIds(self):
  return list(self.functions.keys())



# Trida jedne funkce. Vraci hodnoty.
class Function(ComputingClass):
 name = 'FUNC'
 
 # Vytvoří výpočtovou část funkce. Uloží údaje (předpis, barvu) a upraví předpis pro výpočet.
 def __init__(self, fid, exprSrc, exprFin=None, number=0):
  self.setBasic(fid, number)
  exprSrc = exprSrc.replace('^', '**') # bugfix - v Tkinteru ^ nejak nefacha
  if exprFin is None:
   self.setExpr(exprSrc, *Function.prepareExpr(exprSrc))
  else:
   self.setExpr(exprSrc, exprFin, Function.findPars(exprFin))

 def setBasic(self, fid, number):
  self.fid = fid
  self.setNumber(number)
  self.steps = conf.get('gridpar', 'compute-steps')
  self.lineWidth = conf.get('gridpar', 'normal-function-linewidth')
  self.pars = []
  self.parametric = False
  self.parValues = []

 def edit(self, exprSrc):
  exprSrc = exprSrc.replace('^', '**')
  self.setExpr(exprSrc, *Function.prepareExpr(exprSrc))
 
 def setExpr(self, exprSrc, exprFin, pars):
  self.exprFin = exprFin
  self.pars = pars
  if self.pars:
   self.parametric = True
   self.parValues = [conf.get('gridpar', 'par-init-value')]*len(self.pars)
  if exprSrc[0] == 'y':
   self.exprSrc = exprSrc
  else:
   self.exprSrc = 'y = ' + exprSrc
  self.name += '-' + self.exprSrc
  message = Function.exprErrorTest(self.exprFin, self.pars)
  if message:
   raise FunctionError(message)
  self.function = Function.evalFunction(self.exprFin, self.pars)
 
  
 # Vrací hodnotu funkce v daném bodě, pro nedefinovanou hodnotu a imag. číslo None.
 def getValue(self, x, **par):
  try:
   res = self.function(x, **par)
   if type(res) is type(1j): return None
   else: return res
  except (ArithmeticError, ValueError, TypeError):
   return None
  except Exception as message:
   self.deleteSelf()
   raise FunctionError(message)
 
 # Vrací ID funkce.
 def getFID(self):
  return self.fid
 
 # Nastavuje pořadové číslo funkce (vnější reprezentace, vazba na barvu).
 def setNumber(self, number):
  self.number = number
  self.colour = conf.getFuncColour(number)
 
 # Nastavuje uživatelskou barvu funkce.
 def setColor(self, color):
  self.colour = color

 # Vrací pořadové číslo funkce (pro výpis).
 def getNumber(self):
  return self.number
   
 # Vrací reprezentaci výrazu pro vnější zobrazení.
 def getExpr(self):
  return self.exprSrc
 
 def getExprFin(self):
  return self.exprFin
 
 def getColour(self):
  return self.colour
 
 def setLineWidth(self, width):
  self.lineWidth = width
 
 def getLineWidth(self):
  return self.lineWidth
 
 def getPars(self):
  return self.pars
 
 def isParametric(self):
  return self.parametric
 
 def getParValue(self, par):
  return self.parValues[self.pars.index(par)]
 
 def setParValue(self, par, value):
  self.parValues[self.pars.index(par)] = value
  self.count()
  mgr.replotFunction(self.fid)
 
 # Podle hranic pole vytvoří uspořádané dvojice výsledků - hodnot
 def count(self):
  self.reset()
  newDiff = 0
  parDict = base.mapToDict(self.pars, self.parValues)
  for i in range(self.steps + 1):
   oldDiff = newDiff
   newX = self.lowBorder + (self.resolution * i)
   newY = self.getValue(newX, **parDict)
   if self.y and self.y[-1] is not None and newY is not None:
    newDiff = abs(newY - self.y[-1])
   if abs(newDiff - oldDiff) > self.yRange:
    self.x.append(newX - self.resolution / 2)
    self.y.append(None)
    self.pointList.append([]) # nedefinovana hodnota - dalsi usek cary
   self.x.append(newX)
   self.y.append(newY)
   if newY is None:
    self.pointList.append([])
   else:
    self.pointList[-1].append(comp.getXPx(newX))
    self.pointList[-1].append(comp.getYPx(newY))
 
 def reset(self):
  self.x = []
  self.y = []
  self.pointList = [[]]
  self.lowBorder = comp.getXMinus()
  self.highBorder = comp.getXPlus()
  self.range = self.highBorder - self.lowBorder
  self.resolution = self.range / self.steps
  self.yRange = comp.getYRange()

 def getPoints(self):
  return self.pointList
 
 def deleteSelf(self):
  fman.deleteFunction(self.getFID())
 
 
 # Test korektnosti předpisu funkce.
 @staticmethod
 def exprErrorTest(exprFin, pars):
  try:
   function = Function.evalFunction(exprFin, pars)
  except Exception as message:
   return message
  else:
   return False

 # Vrací z předpisu objekt funkce.
 @staticmethod
 def evalFunction(exprFin, pars):
  parStr = Function.getParStr(pars)
  return eval('lambda {par}: {ex}'.format(par=parStr, ex=exprFin))
 
 # Sestavuje řetězec ze seznamu parametrů.
 @staticmethod
 def getParStr(pars):
  parStr = 'x'
  for par in pars:
   parStr += (', ' + par)
  return parStr

 # Hledá v předpisu parametry.
 @staticmethod
 def findPars(exprFin):
  pars = []
  for par in Function.PARS:
   if exprFin.find('(' + par + ')') != -1:
    pars.append(par)
  return pars

 # Připravuje předpis pro počítačový výpočet.
 @staticmethod
 def prepareExpr(expr):
  expr = ''.join(expr.split(' ')) # bez mezer
  for i in range(len(Function.EXPR_SUBPATT)):
   expr = expr.replace(Function.EXPR_SUBPATT[i], Function.EXPR_SUBSUBST[i])
  for i in range(len(Function.EXPR_REGPATT)):
   while re.search(Function.EXPR_REGPATT[i], expr):
    expr = re.sub(Function.EXPR_REGPATT[i], Function.EXPR_REGFUNC[i], expr)
    break
  print(expr)
  return expr, Function.findPars(expr)
 
 # Kouskuje předpis.
 @staticmethod
 def preparePart(rec):
  all = rec.group(0)
  parEnd = Function.endOfParth(all)
  return (all[:parEnd], all[parEnd:])

 # Detekuje přebytečné závorky.
 @staticmethod
 def endOfParth(all):
  opens = 0
  closes = 0
  for i in range(len(all)):
   if all[i] == '(':
    opens += 1
   elif all[i] == ')':
    closes += 1
   if closes == opens and opens != 0:
    return i+1
 
 # Upravuje zápis odmocnin.
 @staticmethod
 def substRoot(rec):
  toSubst, hang = Function.preparePart(rec)
  mainExpr = '(' + toSubst[4:].split('(', 1)[-1][:-1] + ')**(1/(' + toSubst[4:].split('(')[0] + '))'
  return mainExpr + hang
 
 # Upravuje zápis logaritmů.
 @staticmethod
 def substLog(rec):
  toSubst, hang = Function.preparePart(rec)
  mainExpr = 'math.log(' + toSubst[3:].split('(', 1)[-1][:-1] + ', (' + toSubst[3:].split('(')[0] + '))'
  return mainExpr + hang
 
 # Násobení .
 @staticmethod
 def substTiming(rec, aft):
  toSubst = rec.group(0)
  return '(' + toSubst.split(aft, 1)[0] + ')*' + aft
 
 # Násobení .
 @staticmethod
 def substAbsOverflow(rec):
  toSubst = rec.group(0)
  return toSubst[:-2] + toSubst[-1]
 
 # Slovníky určující substituce předpisu pro výpočet.
 EXPR_SUBPATT = [',',  'X', 'x',   'A', 'a',   'B', 'b',   'C', 'c',   'D', 'd',   'sin',      '(c)os',    't(a)n',    '(c)o', 'tg',       ')(',  ')|',  ')[',  'log(',   'ln',       'sqrt',  'pi',      'e',      '(a)r(c)math.', 'sgn',        '(a)*(b)s']
 EXPR_SUBSUBST = ['.', 'x', '(x)', 'a', '(a)', 'b', '(b)', 'c', '(c)', 'd', '(d)', 'math.sin', 'math.cos', 'math.tan', '1/',   'math.tan', ')*(', ')*|', ')*[', 'log10(', 'math.log', 'root2', 'math.pi', 'math.e', 'math.a',       'mathfx.sgn', 'abs']
 EXPR_REGPATT = [r'log\([0-9xabcd.]+\)\*\(', r'root\([0-9xabcd.]+\)\*\(', r'log[0-9xabcd.]+\(.+\)', r'root[0-9xabcd.]+\(.+\)', r'[0-9.]+\(', r'[0-9xabcd.]+\|', r'\|.+?\*\|', r'[0-9xabcd.]+\[', r'\|.+?\|', r'\[.+?\]']
 EXPR_REGFUNC = [(lambda x: 'log' + x.group(0)[4:-3] + '('),
   (lambda x: 'root' + x.group(0)[5:-3] + '('),
   lambda x: Function.substLog(x), # meni log2(3) na math.log(3, 2) - NETBU (Not Expected To Be Understood)
   lambda x: Function.substRoot(x), # meni root3(5) na (5)**(1/3) - NETBU
   lambda x: Function.substTiming(x, '('), # meni 2.5(...) na (2.5)*(...)
   lambda x: Function.substTiming(x, '|'), # meni 2.5|...| na (2.5)*|...|
   lambda x: Function.substAbsOverflow(x), # meni |...*| na |...|
   lambda x: Function.substTiming(x, '['), # meni 2.5[...] na (2.5)*[...]
   (lambda x: 'abs(' + x.group(0)[1:-1] + ')'), # nahrazeni |2x| za abs(2x) - NA KONEC!
   (lambda x: 'int(' + x.group(0)[1:-1] + ')')] # nahrazeni [x] za int(x)
 PARS = ['a', 'b', 'c', 'd']

  
class PlotComputer(ComputingClass):
 # Parametry plátna:
 # W zastupuje X nebo Y, funguje obojí, podobně Q W/H)
 #
 # QVAL - rozměr plátna
 # WDIM - hodnoty, které se mají na osu vejít (číselně) - WDIM = WCOUNT2 * WSCALE
 # WCOUNT2 - počet normálních čar, které se mají na obrazovku vejít (bez ohledu na měřítko)
 # WSCALE - měřítko osy (kolikrát je zvětšeno oproti normálu), CONF - default-scale
 # WUNITPX - jednotka osy (převod hodnot na pixely - kolik pixelů má 1)
 # UNIT2 - vzdálenost mezi dvěma hlavními (normálními) čarami mřížky, platí UNIT2 = WUNITPX * WSCALE, UNIT2 = QVAL // WCOUNT2
 # UNIT1 - vzdálenost mezi dvěma čarami mřížky (malými), platí UNIT1 = UNIT2 * DIM1 (CONF - minor-grid)
 # UNIT3 - vzdálenost mezi zvýrazněnými čarami mřížky, platí UNIT3 = UNIT2 * DIM3 (CONF - major-grid)
 # QHANG - "převis" - místa mezi krajními čarami mřížky a okraji plátna - obsolete
 # QSTART - místo mezi prvním okrajem plátna a první čarou mřížky (levá část přesahu) - QSTART@INIT = QHANG * FIRSTHANGPART (CONF)
 # WAXISORD - pořadí osy v mřížce
 # WZERO - pozice osy
 # WMINUS - počet jednotek na přísl. ose do minusu
 # WPLUS - počet jednotek na přísl. ose do plusu
 #
 # Musí platit QVAL = WCOUNT2 * WUNIT2 + QHANG.
 # První čára mřížky má rozměr QSTART.
 # Přibližování popisku čáře má na starosti CLOSERFONT.
 #
 # Měnit se může:
 # Rozměry plátna - s velikostí okna - QVAL
 # Měřítko - taky nějaký posuvník (ale i pro každou osu zvlášť) - WSCALE
 # Pozice středu - myší po ploše, nutno plynule - WZERO
 #

 def __init__(self):
  # Inicializace hodnot
  self.wVal = 0
  self.hVal = 0
  self.xZero = 0
  self.yZero = 0
  self.unit1 = 0
  self.zoneSpace = 0
  # Stavové proměnné počítání
  self.xPiScale = False
  # (Více/méně) konstanty rozměrů mřížky
  self.xCount2 = conf.get('gridpar', 'x-normal-count')*2
  self.xScale = conf.get('gridpar', 'default-scale')
  self.yScale = conf.get('gridpar', 'default-scale')
  self.dim1 = conf.get('gridpar', 'minor-grid')
  self.dim3 = conf.get('gridpar', 'major-grid')
  

 #
 # Setters (TOP)
 #
 
 # QVAL set
 def setVals(self, wVal, hVal):
  self.valWSet(wVal)
  self.valHSet(hVal)
  self.valsCount()
 
 # DIM3 set
 def setMajorDimension(self, dim):
  self.dim3 = dim

 # WSCALE setters
 # WSCALE direct set
 def setBothScales(self, value):
  self.xPiScale = False
  self.scaleXModify(value)
  self.scaleYModify(value)
  self.scaleCount()
 
 # XSCALE direct set
 def setXScale(self, value):
  self.scaleXModify(value)
  self.scaleCount()
 
 def setXPiScale(self, mult):
  self.xPiScale = True
  self.xPiQuot = mult
  self.scaleXModify(conf.getPi() / mult)
  self.scaleCount()
  
 # YSCALE direct set
 def setYScale(self, value):
  self.scaleYModify(value)
  self.scaleCount()
 
 # WSCALE increase (in) - ZOOM
 def zoomBothIn(self):
  self.multZoom(1/conf.get('gridpar', 'scale-multiplier'))
 
 # WSCALE decrease (out) - ZOOM   
 def zoomBothOut(self):
  self.multZoom(conf.get('gridpar', 'scale-multiplier'))
  
 # XSCALE increase (in)
 def zoomXIn(self):
  self.multXScale(1/conf.get('gridpar', 'scale-multiplier'))

 # XSCALE decrease (out)
 def zoomXOut(self):
  self.multXScale(conf.get('gridpar', 'scale-multiplier'))

 # YSCALE increase (in)
 def zoomYIn(self):
  self.multYScale(1/conf.get('gridpar', 'scale-multiplier'))

 # YSCALE decrease (out)
 def zoomYOut(self):
  self.multYScale(conf.get('gridpar', 'scale-multiplier'))


 # WZERO setters
 # XZERO adding (scroll)
 def zeroXAdd(self, add):
  self.zeroXSet(self.xZero + add)
 
 # YZERO adding (scroll)
 def zeroYAdd(self, add):
  self.zeroYSet(self.yZero + add)
 
 # XZERO multiplying (vals change)
 def zeroXMult(self, mult):
  self.zeroXSet(self.xZero * mult)

 # YZERO multiplying (vals change)
 def zeroYMult(self, mult):
  self.zeroYSet(self.yZero * mult)
 
 # CENTER (center the zeros, as on init)
 def center(self):
  self.centerCount()
 
 # FILERESET (file loaded, adjust grid options)
 def fileReset(self, imp):
  self.zeroXSet(self.wVal * imp.getWFactor())
  self.zeroYSet(self.hVal * imp.getHFactor())
  xPiQuot = imp.getXPiQuot()
  if xPiQuot == 0:
   panel.setXScale(imp.getXScale())
  else:
   panel.setXPiScale(xPiQuot)
  panel.setYScale(imp.getYScale())


 # 
 # Setters (INNER)
 #
 
 # WVAL set and modif factor
 def valWSet(self, val):
  if self.wVal == 0:
   wFactor = 1
  else:
   wFactor = val / self.wVal
  self.wVal = val
  self.zeroXMult(wFactor)
 
 # HVAL set and modif factor
 def valHSet(self, val):
  if self.hVal == 0:
   hFactor = 1
  else:
   hFactor = val / self.hVal
  self.hVal = val
  self.zeroYMult(hFactor)


 # Scale/zoom methods
 # WSCALE ZOOM (stick-to-centre)
 def multZoom(self, zoom):
  self.zeroXZoom(zoom)
  self.zeroYZoom(zoom)
  self.xPiScale = False
  self.scaleXMultiply(zoom)
  self.scaleYMultiply(zoom)
  self.scaleCount()
 
 # XSCALE multiply and recount
 def multXScale(self, zoom):
  self.scaleXMultiply(zoom)
  self.scaleCount()
 
 # YSCALE multiply and recount
 def multYScale(self, zoom):
  self.scaleYMultiply(zoom)
  self.scaleCount()
 
 # Scale bottom modifiers
 # XSCALE modify
 def scaleXModify(self, value):
  self.xScale = value

 # YSCALE modify
 def scaleYModify(self, value):
  self.yScale = value
 
 # XSCALE multiply
 def scaleXMultiply(self, mult):
  self.xScale *= mult
 
 # YSCALE multiply
 def scaleYMultiply(self, mult):
  self.yScale *= mult


 # WZERO moving to keep the centre unmoved (when ZOOMING)
 # XZERO zoom
 def zeroXZoom(self, zoom):
  self.zeroXSet((self.wVal // 2) * (1 - (1 / zoom)) + self.xZero / zoom)
 
 # YZERO zoom
 def zeroYZoom(self, zoom):
  self.zeroYSet((self.hVal // 2) * (1 - (1 / zoom)) + self.yZero / zoom)


 # WZERO setters
 # XZERO modified
 def zeroXSet(self, value):
  self.xZero = int(value)
  self.xAxis, self.leftDeadZone, self.rightDeadZone = self.verifyZero(self.xZero, self.wVal)

 # YZERO modified
 def zeroYSet(self, value):
  self.yZero = int(value)
  self.yAxis, self.topDeadZone, self.bottomDeadZone = self.verifyZero(self.yZero, self.hVal)
 
 # verifying WZERO (checking deadzones)
 def verifyZero(self, zero, qVal):
  if zero <= self.zoneSpace:
   return (self.zoneSpace, self.zoneSpace, 0)
  elif zero >= (qVal - self.zoneSpace):
   return ((qVal - self.zoneSpace), 0, self.zoneSpace)
  else:
   return (zero, 0, 0)


 #
 # Counting (EVTBIND)
 #

 # INIT
 def firstCount(self):
  self.countUnits()
  self.initZeros()
  self.countPxConverters()
  self.countGrid()

 # QVAL changed
 def valsCount(self):
  self.countUnits()
  self.countPxConverters()
  self.countGrid()
 
 # WSCALE changed
 def scaleCount(self):
  self.countPxConverters()
  self.countGrid()

 # WZERO changed and verified
 def scrollCount(self):
  self.countGrid()
 
 # WZERO initializing (centered)
 def centerCount(self):
  self.initZeros()
  self.countGrid()
 
 def edgeCount(self):
  self.edgeZeros()
  self.countGrid()
 
 def bottomCount(self):
  self.bottomZeros()
  self.countGrid()

 def cornerCount(self):
  self.cornerZeros()
  self.countGrid()
 
 #
 # Counting (PARTS)
 #
 
 # Základní - počítá hustotu a poměry čar
 # závisí na QVAL
 def countUnits(self):
  self.unit1 = self.wVal // (self.xCount2 * self.dim1)
  self.unit2 = self.unit1 * self.dim1
  self.strokeLen = self.unit1 // conf.get('gridpar', 'stroke-length-ratio')
  self.zoneSpace = int(self.unit1 * conf.get('gridpar', 'deadzone-space-multiplier'))
 
 # Počítá převod mezi pixely a číselnými hodnotami
 # závisí na QVAL a WSCALE
 def countPxConverters(self):
  self.xUnitPx = self.unit2 / self.xScale
  self.yUnitPx = self.unit2 / self.yScale
 
 # Inicializuje pozici os (start nebo vystředění)
 # závisí na QVAL
 def initZeros(self):
  self.xZero = self.wVal // 2
  self.yZero = self.hVal // 2
  self.xAxis = self.wVal // 2
  self.yAxis = self.hVal // 2
  self.leftDeadZone = 0
  self.rightDeadZone = 0
  self.topDeadZone = 0
  self.bottomDeadZone = 0
 
 def edgeZeros(self):
  self.zeroXSet(self.unit1 * int(math.ceil(conf.get('gridpar', 'deadzone-space-multiplier'))))
  self.zeroYSet(self.hVal // 2)

 def bottomZeros(self):
  self.zeroXSet(self.wVal // 2)
  self.zeroYSet(self.hVal - self.unit1 * int(math.ceil(conf.get('gridpar', 'deadzone-space-multiplier'))))

 def cornerZeros(self):
  dist = self.unit1 * int(math.ceil(conf.get('gridpar', 'deadzone-space-multiplier')))
  self.zeroXSet(dist)
  self.zeroYSet(self.hVal - dist)
 
 # Počítá rozložení místa a čar mřížky
 # závisí na úplně všem
 def countSpaces(self):
  # misto za osami
  self.xLeft = self.xAxis - self.leftDeadZone
  self.xRight = self.wVal - (self.xAxis + self.rightDeadZone)
  self.yTop = self.yAxis - self.topDeadZone
  self.yBottom = self.hVal - (self.yAxis + self.bottomDeadZone)
  # pocet car pred a za osami
  self.xLinesLeft = self.xLeft // self.unit1
  self.xLinesRight = (self.xRight // self.unit1) + 2
  self.yLinesTop = self.yTop // self.unit1
  self.yLinesBottom = (self.yBottom // self.unit1) + 2
  # misto pred prvni carou
  if self.leftDeadZone:
   self.wStart = self.xZero + (abs(self.xZero) // self.unit1 + 1) * self.unit1
  else:
   self.wStart = abs(self.xZero) % self.unit1
  if self.topDeadZone:
   self.hStart = self.yZero + (abs(self.yZero) // self.unit1 + 1) * self.unit1
  else:
   self.hStart = abs(self.yZero) % self.unit1
 
 # Počítá rozsahy zobrazení pro kalkulaci funkčních předpisů
 # závisí na úplně všem 
 def countRanges(self):
  # kalkulace rozsahu zobrazeneho
  self.yAxisOrd = (self.xZero - self.wStart) // self.unit1
  self.xAxisOrd = (self.yZero - self.hStart) // self.unit1
  self.xMinus = -(self.xZero / self.xUnitPx)
  self.xPlus = (self.wVal - self.xZero) / self.xUnitPx
  self.yMinus = -(self.hVal - self.yZero) / self.yUnitPx
  self.yPlus = self.yZero / self.yUnitPx
 
 # Sjednocovač pro SPACES a RANGES (nikdy nejdou zvlášť) - a funkce jsou k nim prilepeny take
 def countGrid(self):
  self.countSpaces()
  self.countRanges()
  fman.countFunctions()
 
 
 #
 # Other Methods (Computing, but not closely related to grid)
 #
  
 # Počítá popisky obsahující pí
 def getPiLabel(self, coor):
  numtr = self.getXPiMult(coor)
  if numtr == 0: return '0'
  dnmtr = int(self.xPiQuot)
  if dnmtr == self.xPiQuot and int(numtr) == numtr:
   fraction = [int(numtr), dnmtr]
   divisor = mathfx.gcd(*fraction)
   for i in range(len(fraction)):
    fraction[i] = str(fraction[i] // divisor)
    if fraction[i] == '1':
     fraction[i] = ''
   numtr, dnmtr = fraction
   if numtr == '-1': numtr = '-'
   if dnmtr != '': dnmtr = '/' + dnmtr
   return numtr + conf.get('out', 'x-pi') + dnmtr
  else:
   return String.floatStr(numtr / self.xPiQuot) + conf.get('out', 'x-pi')
  
 #
 # Getters (to actually get something out of all this stuff)
 #
 
 def getXMinus(self):
  return self.xMinus
 
 def getYMinus(self):
  return self.yMinus
 
 def getXPlus(self):
  return self.xPlus
 
 def getYPlus(self):
  return self.yPlus

 def getYRange(self):
  return abs(self.yMinus - self.yPlus)
 
 def getXScale(self):
  return self.xScale
 
 def getYScale(self):
  return self.yScale
 
 def getPiScale(self):
  return self.xPiScale
 
 def getXPiQuot(self):
  if self.xPiScale: return self.xPiQuot
  else: return 0
 
 def getXAxis(self):
  return self.xAxis
 
 def getYAxis(self):
  return self.yAxis
 
 def getXZero(self):
  return self.xZero
 
 def getYZero(self):
  return self.yZero
 
 def getXAxisOrd(self):
  return self.xAxisOrd
 
 def getYAxisOrd(self):
  return self.yAxisOrd
 
 def getWVal(self):
  return self.wVal
 
 def getHVal(self):
  return self.hVal
 
 def getWFactor(self):
  return self.xZero / self.wVal
 
 def getHFactor(self):
  return self.yZero / self.hVal
 
 def getStrokeLength(self):
  return self.strokeLen
 
 def getXNum(self, xPx):
  return (xPx - self.xZero) / self.xUnitPx
 
 def getXPiMult(self, xPx):
  return (xPx - self.xZero) / self.unit2
 
 def getYNum(self, yPx):
  return (self.yZero - yPx) / self.yUnitPx
 
 def getXPx(self, xNum):
  return int((xNum * self.xUnitPx) + self.xZero)
 
 def getYPx(self, yNum):
  return int(self.yZero - (yNum * self.yUnitPx))
 
 def getMinorDim(self):
  return self.dim1
 
 def getMajorDim(self):
  return self.dim3
 
 def getMinorUnit(self):
  return self.unit1
 
 def getWStart(self):
  return self.wStart
 
 def getHStart(self):
  return self.hStart
 
 def getDeadZones(self):
  return (bool(self.leftDeadZone), bool(self.rightDeadZone), bool(self.topDeadZone), bool(self.bottomDeadZone))



class Manager(ComputingClass):
 def __init__(self):
  # Stavové proměnné pohybu
  self.scrolling = False
  self.motionLines = False
  self.scrollBegin = (0, 0)

 #
 # Event Handlers
 #

 # Zmena velikosti platna (prepocet mrizky)
 def valsChanged(self, wVal, hVal):
  comp.setVals(wVal, hVal)
  self.replot()
 
 # Zmena polohy kurzoru na platne (pro zobrazeni polohy)
 def cursorMoved(self, x, y):
  self.motion(x, y)

 # Posun kurzoru mimo platno (konec zobrazovani polohy)
 def motionEnd(self):
  self.endMotion()

 # Stlaceni leveho tlacitka a drzeni (zacatek posunu)
 def scrollStart(self, x, y):
  self.startScroll(x, y)
 
 # Pusteni leveho tlacitka mysi (konec scrollu)
 def scrollEnd(self, x, y):
  if self.scrolling:
   self.endScroll(x, y)
 
 # Pravy klik na platno (deselect funkce)
 def functionUnselected(self):
  self.unselectFunction(doList=True)
 
 # Stisk Delete (smazání funkce)
 def deletePressed(self):
  self.deleteFunction()
 
 # Zoomy z Panelu - přesměrování na Computer a replot
 def setBothScales(self, value):
  comp.setBothScales(value)
  self.replot()
 
 def setXScale(self, value):
  comp.setXScale(value)
  self.replot()
 
 def setXPiScale(self, mult):
  comp.setXPiScale(mult)
  self.replot()
  
 def setYScale(self, value):
  comp.setYScale(value)
  self.replot()
 
 def zoomBothIn(self):
  comp.zoomBothIn()
  self.replot()
 
 def zoomBothOut(self):
  comp.zoomBothOut()
  self.replot()
  
 def zoomXIn(self):
  comp.zoomXIn()
  self.replot()

 def zoomXOut(self):
  comp.zoomXOut()
  self.replot()

 def zoomYIn(self):
  comp.zoomYIn()
  self.replot()

 def zoomYOut(self):
  comp.zoomYOut()
  self.replot()

 # Panel button zero normalizing
 def scrollCenter(self):
  comp.centerCount()
  self.replot()
 
 def scrollEdge(self):
  comp.edgeCount()
  self.replot()
 
 def scrollBottom(self):
  comp.bottomCount()
  self.replot()

 def scrollCorner(self):
  comp.cornerCount()
  self.replot()
 
 def zoomNormalize(self):
  self.setBothScales(conf.get('gridpar', 'default-scale'))
  panel.zoomNormalize()
 
 def newCommand(self):
  pass
 
 def openCommand(self):
  openFile = win.getOpenFileName()
  if openFile != '':
   main.setFilePath(openFile)
   imp = Importer(filePath=main.getFilePath())
   imp.load()
   self.loadData(imp)
 
 def saveCommand(self):
  if main.getFileName() == main.getDefaultFileName():
   saveFile = win.getSaveFileName()
   if saveFile != '':
    main.setFilePath(filePath=saveFile)
    Exporter(filePath=main.getFilePath()).save()
  else:
   Exporter(filePath=main.getFilePath()).save()
 
 def saveAsCommand(self):
  saveFile = win.getSaveFileName()
  if saveFile != '':
   main.setFilePath(filePath=saveFile)
   Exporter(filePath=main.getFilePath()).save()
 
 def closeCommand(self):
  pass
 
 def exitCommand(self):
  main.exit()
 
 def scrollCenterCommand(self):
  self.scrollCenter()
 
 def scrollEdgeCommand(self):
  self.scrollEdge()

 def scrollCornerCommand(self):
  self.scrollCorner()

 def scrollBottomCommand(self):
  self.scrollBottom()

 def zoomNormalCommand(self):
  self.zoomNormalize()
 
 def gridNormalCommand(self):
  self.scrollCenter()
  self.zoomNormalize()
  
 
 #
 # Main Action Procedures (A Command Processing Scheme)
 #
 
 # Starting
 def start(self):
  plot.display()
  panel.display()
  comp.valWSet(plot.getCanvasWidth())
  comp.valHSet(plot.getCanvasHeight())
  comp.firstCount()
  self.replot()
 
 def loadData(self, imp):
  comp.fileReset(imp)
  self.deleteAllFunctions()
  flist = imp.getFunctionList()
  for fid in flist.keys():
   self.loadFunction(fid, *flist[fid])
  self.replot()
 
 # Cursor motion - update motion indicators (and scroll, if scrolling)
 def motion(self, x, y):
  if self.motionLines:
   self.plotMotionLines(x, y)
  panel.motion(comp.getXNum(x), comp.getYNum(y), self.scrolling)
  if self.scrolling:
   self.plotScrollLines((comp.getXZero() + x - self.scrollBegin[0]), (comp.getYZero() + y - self.scrollBegin[1]))

 # Cursor out of canvas - erase motion indicators
 def endMotion(self):
  plot.eraseMotionLines()
  panel.motionEnd()
 
 # Click and hold - scroll started, save start position and display movement (dx, dy)
 def startScroll(self, x, y):
  self.scrolling = True
  panel.scrollStart(comp.getXNum(x), comp.getYNum(y))
  self.scrollBegin = (x, y)
 
 # Left button released - scroll ended, delete trackers and update grid
 def endScroll(self, x, y):
  panel.scrollEnd()
  comp.zeroXAdd(x - self.scrollBegin[0])
  comp.zeroYAdd(y - self.scrollBegin[1])
  comp.scrollCount()
  self.replot()
  self.scrolling = False
 
 # Create function (panel or program start command)
 def createFunction(self, expr):
  fid = fman.createFunction(expr)
  panel.addFunction(fid)
  self.plotFunction(fid)

 def editFunction(self, fid, expr):
  fman.editFunction(fid, expr)
  panel.updateFunction(fid)
  panel.selectFunction(fid)
  self.replotFunction(fid)
 
 def selectFunction(self, fid):
  oldFID = fman.getSelectedFID()
  fman.selectFunction(fid)
  panel.selectFunction(fid)
  self.replotFunction(fid)
  if oldFID:
   self.replotFunction(oldFID)
 
 def loadFunction(self, fid, number, exprSrc, exprFin):
  fman.loadFunction(fid, number, exprSrc, exprFin)
  panel.addFunction(fid)
  
 # Unselect function (right click or unselect at panel)
 def unselectFunction(self, fid=None):
  fid = fman.verifyFID()
  if fid is not None:
   fman.unselectFunction(fid)
   self.replotFunction(fid)
   panel.unselectFunction()
 
 # Change function color
 def changeFuncColor(self, fid=None, color=None):
  if color is None: return
  else:
   if fid is None:
    fid = fman.getSelectedFID()
   fman.changeFuncColor(color, fid)
   self.replotFunction(fid)

 # Delete function after all
 def deleteFunction(self, fid):
  fman.deleteFunction(fid)
  self.eraseFunction(fid)
  panel.removeFunction(fid)
  
 # Unmap all functions...
 def deleteAllFunctions(self):
  for fid in fman.getFunctionIds():
   self.deleteFunction(fid)
  fman.resetFunctionOrds()

 # Erase Function (just removing from the canvas)
 def eraseFunction(self, fid):
  plot.eraseFunction(fid)

 # Switch motion lines appearance (panel checkbox)
 def switchMotionLines(self):
  self.motionLines = not self.motionLines
 
 # Main updater...
 def replot(self):
  self.replotGrid()
  self.plotFunctions()
 
 
 #
 # Grid Plotting
 #
 
 def replotGrid(self):
  self.eraseGrid()
  self.plotGrid()
 
 def plotFunctions(self):
  for fid in fman.getFunctionIds():
   self.plotFunction(fid)
 
 def replotFunction(self, fid):
  self.eraseFunction(fid)
  self.plotFunction(fid)

 # zrobi mrizku podle aktualnich parametru (nepocita nic)
 def plotGrid(self):
  self.plotDeadZones()
  self.plotXGrid()
  self.plotYGrid()

 def plotXGrid(self):
  # vytvari cary v x-smeru (tedy konstanty, lisici se y-souradnici)
  self.plotDirGrid(comp.getHStart(), comp.getHVal(), self.plotXGridMark)
    
 def plotYGrid(self):
  # vytvari cary v y-smeru (tedy nefunkce, lisici se x-souradnici)
  self.plotDirGrid(comp.getWStart(), comp.getWVal(), self.plotYGridMark)
 
 def plotDirGrid(self, start, end, plotFunc):
  i = 0
  coor = start
  while coor <= end:
   plotFunc(coor, i)
   coor += comp.getMinorUnit()
   i += 1
  
 def eraseGrid(self):
  plot.eraseGrid()
   
   
 def plotDeadZones(self):
  left, right, top, bottom = comp.getDeadZones()
  # osni zona nahore/dole
  if top:
   self.plotTopDeadZone()
  elif bottom:
   self.plotBottomDeadZone()
  # osni zona vlevo/vpravo
  if left:
   self.plotLeftDeadZone()
  elif right:
   self.plotRightDeadZone()
  # osni cary (Axis)
  if top or bottom:
   plot.plotHDeadZoneLine()
  if left or right:
   plot.plotWDeadZoneLine()
 
 
 # Upper Plot Commands (Still some computing involved...)
 # Čáry a popisky os
 def plotXGridMark(self, coor, i):
  plotState = self.getGridMarkType(i, comp.getXAxisOrd())
  lineColour = self.getLineColour(plotState)
  if lineColour is not None:
   plot.plotXGridLine(coor, lineColour)
  if (plotState & 1) == 1:
   plot.plotXGridStroke(coor)
  if (plotState & 2) == 2:
   self.plotYLabel(coor)

 def plotYGridMark(self, coor, i):
  plotState = self.getGridMarkType(i, comp.getYAxisOrd())
  lineColour = self.getLineColour(plotState)
  if lineColour is not None:
   plot.plotYGridLine(coor, lineColour)
  if (plotState & 1) == 1:
   plot.plotYGridStroke(coor)
  if (plotState & 2) == 2:
   self.plotXLabel(coor)
 
 # vybira barvu cary podle poradi (osa, vetsi, normal, mensi)
 def getGridMarkType(self, i, axisOrd):
  # Konstanta PLOT - bitový ukazatel:
  # 0 - nevyrábět vůbec
  # 1 - malá čárka (Stroke)
  # 2 - popisek (Label)
  # 4 - velmi slabá čára (Line 1)
  # 8 - slabší čára (Line 2)
  # 16 - silnější čára (Line 3)
  # 32 - silná čára (Line 4) - osy
  # Přidání vlastnosti: PLOT |= vlastnost
  # Odebrání vlastnosti: PLOT &= ~vlastnost
  # Ověření vlastnosti: (PLOT & vlastnost) == vlastnost
  if i == axisOrd:
   return conf.get('gridpar', 'axis-grid-plot')
  elif (i - axisOrd) % (comp.getMinorDim() * comp.getMajorDim()) == 0:
   return conf.get('gridpar', 'major-grid-plot')
  elif (i - axisOrd) % comp.getMinorDim() == 0:
   return conf.get('gridpar', 'normal-grid-plot')
  else:
   return conf.get('gridpar', 'minor-grid-plot')
 
 def getLineColour(self, plot):
  if (plot & 4) == 4:
   return conf.get('colour', 'grid-line-1')
  elif (plot & 8) == 8:
   return conf.get('colour', 'grid-line-2')
  elif (plot & 16) == 16:
   return conf.get('colour', 'grid-line-3')
  elif (plot & 32) == 32:
   return conf.get('colour', 'grid-line-4')
  else:
   return None
  
 # Popisky os
 # Osa X
 def plotXLabel(self, coor):
  if comp.getPiScale():
   label = comp.getPiLabel(coor)
  else:
   number = comp.getXNum(coor)
   if int(number) == number:
    label = str(int(number))
   else:
    label = conf.get('out', 'grid-float-labelformat').format(number)
  plot.plotXGridLabel(x=coor, text=label)
 
 # Osa Y
 def plotYLabel(self, coor):
  number = comp.getYNum(coor)
  if int(number) == number:
   label = str(int(number))
  else:
   label = conf.get('out', 'grid-float-labelformat').format(number)
  plot.plotYGridLabel(y=coor, text=label)


 # Funkce
 def plotFunction(self, fid):
  function = fman.getFunction(fid)
  pointsList = function.getPoints()
  for points in pointsList:
   if len(points) < 4: continue
   plot.plotFunctionLine(points, colour=function.getColour(), lineWidth=function.getLineWidth(), fid=function.getFID())

 # Čáry posunu souřadnic
 def plotScrollLines(self, x, y):
  plot.eraseScrollLines()
  plot.plotXScrollLine(y)
  plot.plotYScrollLine(x)
 
 # Čáry posunu kurzoru
 def plotMotionLines(self, x, y):
  plot.eraseMotionLines()
  plot.plotXMotionLine(y)
  plot.plotYMotionLine(x)


 # Mrtvé zóny (místa za osou, která je vlastně někde úplně jinde ;-))
 def plotTopDeadZone(self):
  plot.plotHDeadZoneRect(0, comp.getYAxis())
 
 def plotBottomDeadZone(self):
  plot.plotHDeadZoneRect(comp.getYAxis(), comp.getHVal())
 
 def plotLeftDeadZone(self):
  plot.plotWDeadZoneRect(0, comp.getXAxis())
  
 def plotRightDeadZone(self):
  plot.plotWDeadZoneRect(comp.getXAxis(), comp.getWVal())
 
 
 

class OutputClass(BaseClass):
 pass
 
class GUInterface(OutputClass, tk.Tk):
 def __init__(self, title=None):
  tk.Tk.__init__(self)
  self.X_FILL_PART = conf.get('gridpar', 'x-fill-part')
  self.Y_FILL_PART = conf.get('gridpar', 'y-fill-part')
  self.X_SPACE_PART = (1 - self.X_FILL_PART) / 2
  self.Y_SPACE_PART = (1 - self.Y_FILL_PART) / 8
  self.screenX = self.winfo_screenwidth()
  self.screenY = self.winfo_screenheight()
  self.geometry('{xdim:d}x{ydim:d}+{xdist:d}+{ydist:d}'.format(
   xdim=int(self.screenX*self.X_FILL_PART),
   ydim=int(self.screenY*self.Y_FILL_PART),
   xdist=int(self.screenX*self.X_SPACE_PART),
   ydist=int(self.screenY*self.Y_SPACE_PART)))
  if os.name == 'nt':
   self.wm_state('zoomed')
  self.wm_iconbitmap(conf.get('path', 'icon'))
  self.title(title)
  self.report_callback_exception = errh.handleLoopError


class MainWindow(OutputClass, tk.Frame):
 def __init__(self, master=None, title=None):
  if master is None and title is not None:
   self.master = GUInterface(title)
  elif master is not None:
   self.master = master
  else:
   raise ValueError('window title not provided')
  tk.Frame.__init__(self, master)
  
 def init(self):
  # ramecky pro sizovani widgetu
  self.mainFrame = tk.Frame(self)
  self.bottomFrame = tk.Frame(self)
  self.leftFrame = tk.Frame(self.mainFrame)
  # self.toolFrame = tk.Frame(self.leftFrame, height=20)
  self.canvasFrame = tk.Frame(self.leftFrame, bd=1, relief='groove')
  self.rightFrame = tk.Frame(self.mainFrame)
  global plot, panel
  self.loadImages()
  plot = Plotter(self.leftFrame)
  panel = ControlPanel(self.rightFrame)
  self.menu = MainMenu(self.winfo_toplevel())
 
 # Obrazky na tlacitka
 def loadImages(self):
  self.plusImg = tk.PhotoImage(file=conf.get('path', 'img-plus'))
  self.minusImg = tk.PhotoImage(file=conf.get('path', 'img-minus'))
  self.piImg = tk.PhotoImage(file=conf.get('path', 'img-pi'))
  self.oneImg = tk.PhotoImage(file=conf.get('path', 'img-one'))
  self.centerImg = tk.PhotoImage(file=conf.get('path', 'axis-center'))
  self.edgeImg = tk.PhotoImage(file=conf.get('path', 'axis-side'))
  self.bottomImg = tk.PhotoImage(file=conf.get('path', 'axis-bottom'))
  self.cornerImg = tk.PhotoImage(file=conf.get('path', 'axis-corner'))
 
 def display(self):
  self.pack(fill='both', expand=1)
  self.mainFrame.pack(side='top', fill='both', expand=1)
  self.bottomFrame.pack(side='top', fill='x')
  self.leftFrame.pack(side='left', fill='both', expand=1)
  # self.toolFrame.pack(side='top', fill='x')
  self.canvasFrame.pack(side='top', fill='x')
  self.rightFrame.pack(side='left', fill='y')
  # self.status.display()
  self.menu.display()
 
 def setTitle(self, title):
  self.master.title(conf.get('out', 'window-title').format(title))
 
 def getOpenFileName(self):
  return tkfdia.askopenfilename(defaultextension=('.' + DATAF_EXT), initialdir=conf.get('path', 'data'),
   filetypes=[(conf.get('out', 'all-files'), '*.*'), (conf.get('out', 'fcink-files'), '*.' + DATAF_EXT)])#, file=main.getFileName())
 
 def getSaveFileName(self):
  return tkfdia.asksaveasfilename(defaultextension=('.' + DATAF_EXT), initialdir=conf.get('path', 'data'),
   filetypes=[(conf.get('out', 'all-files'), '*.*'), (conf.get('out', 'fcink-files'), '*.' + DATAF_EXT)])#, file=main.getFileName())
 
 
  

class Plotter(OutputClass, tk.Canvas):
 def __init__(self, master):
  self.master = master
  tk.Canvas.__init__(self, self.master, borderwidth=1,
   background=conf.get('colour', 'canvas-background'), relief='groove')
  self.clickArea = conf.get('gridpar', 'click-area')
  self.bindEvents()
 
 # Zobrazeni
 def display(self):
  self.pack(side='top', fill='both', expand=1)

 # Handlery 
 # Binding
 def bindEvents(self):
  self.bind('<Configure>', self.canvasResized)
  self.bind('<Enter>', self.cursorMoved)
  self.bind('<Leave>', self.cursorOut)
  self.bind('<Motion>', self.cursorMoved)
  self.bind('<Button-1>', self.leftPressed)
  self.bind('<ButtonRelease-1>', self.leftClicked)
  self.bind('<ButtonRelease-3>', self.rightClicked)
  self.bind('<KeyRelease-Delete>', self.deletePressed)
  # self.bind('<KeyRelease-plus>', panel.zoomedBothIn)
  # self.bind('<KeyRelease-minus>', panel.zoomedBothOut)
  # self.bind('<KeyRelease-KP_Add>', panel.zoomedBothIn)
  # self.bind('<KeyRelease-KP_Subtract>', panel.zoomedBothOut)

 # Zmena velikosti platna (prepocet mrizky)
 def canvasResized(self, event):
  mgr.valsChanged(event.width, event.height)
 
 # Zmena polohy kurzoru na platne (pro zobrazeni polohy)
 def cursorMoved(self, event):
  mgr.cursorMoved(event.x, event.y)

 # Posun kurzoru mimo platno (konec zobrazovani polohy)
 def cursorOut(self, event):
  mgr.motionEnd()

 # Stlaceni leveho tlacitka a drzeni (zacatek posunu)
 def leftPressed(self, event):
  mgr.scrollStart(event.x, event.y)
 
 # Levy klik na platno nebo pusteni leveho tlacitka (vyber funkce nebo konec posunu)
 def leftClicked(self, event):
  fid = self.getFunctionByPlace(event.x, event.y)
  if fid:
   mgr.selectFunction(fid)
  mgr.scrollEnd(event.x, event.y)
 
 # Pravy klik na platno (deselect funkce)
 def rightClicked(self, event):
  mgr.unselectFunction()
 
 # Stisk Delete (smazání funkce)
 def deletePressed(self, event):
  mgr.deleteFunctionById()
 
 # Handler Help (primo vazane udalostni metody)
 def getFunctionByPlace(self, x, y):
  objList = self.find_overlapping(x - self.clickArea, y - self.clickArea, x + self.clickArea, y + self.clickArea)
  funcs = self.find_withtag('func')
  fid = None
  for i in objList: # vybere funkci
   if i in funcs:
    fid = i
    break
  if fid is None: return
  for tag in self.gettags(fid):
   if 'func-' in tag:
    return int(tag[5:])


 # Tagging
 def addTag(self, objId, tag):
  self.addtag_withtag(tag, objId)
 
 def tagGrid(self, objId, add=None, next=None):
  self.addTag(objId, 'grid')
  if add is not None:
   self.addTag(objId, 'grid-' + add)
  if next is not None:
   if type(next) is type([]):
    for text in next:
     self.addTag(objId, text)
   else:
    self.addTag(objId, next)
 
 def tagFunction(self, lid, fid):
  self.tagGrid(lid, next=['func', 'func-{0:d}'.format(fid)])
 
 def tagDeadZone(self, rid):
  self.tagGrid(rid, next='dead-zone')
 
 # Erasing
 def eraseGrid(self):
  self.delete('grid')
  
 def eraseFunction(self, fid):
  self.delete('func-{0:d}'.format(fid))
 
 def eraseMotionLines(self):
  self.delete('motion')
   
 def eraseScrollLines(self):
  self.delete('scroll')
 
   
 # Plot Work
 # Lines
 def plotLine(self, *args, **kwargs):
  return self.create_line(*args, **kwargs)

 def plotXLine(self, yPos, colour='black'):
  return self.plotLine(0, yPos, comp.getWVal(), yPos, fill=colour)

 def plotYLine(self, xPos, colour='black'):
  return self.plotLine(xPos, 0, xPos, comp.getHVal(), fill=colour)
 
 def plotXStroke(self, yPos):
  return self.plotLine((comp.getXAxis() - comp.getStrokeLength()), yPos,
   (comp.getXAxis() + comp.getStrokeLength() + 1), yPos, fill=conf.get('colour', 'grid-line-4'))
  
 def plotYStroke(self, xPos):
  return self.plotLine(xPos, (comp.getYAxis() - comp.getStrokeLength()),
   xPos, (comp.getYAxis() + comp.getStrokeLength() + 1), fill=conf.get('colour', 'grid-line-4'))
 
 # Grid lines
 def plotXGridLine(self, yPos, colour):
  self.tagGrid(self.plotXLine(yPos, colour), add='x')
 
 def plotYGridLine(self, xPos, colour):
  self.tagGrid(self.plotYLine(xPos, colour), add='y')
 
 def plotXGridStroke(self, yPos):
  self.tagGrid(self.plotXStroke(yPos), add='x')
 
 def plotYGridStroke(self, xPos):
  self.tagGrid(self.plotYStroke(xPos), add='y')
 
 # Scroll and Motion lines
 def plotXMotionLine(self, y):
  self.tagGrid(self.plotXLine(y, conf.get('colour', 'grid-line-motion')), next='motion')
 
 def plotYMotionLine(self, x):
  self.tagGrid(self.plotYLine(x, conf.get('colour', 'grid-line-motion')), next='motion')  
  
 def plotXScrollLine(self, y):
  self.tagGrid(self.plotXLine(y, conf.get('colour', 'grid-line-scroll')), next='scroll')

 def plotYScrollLine(self, x):
  self.tagGrid(self.plotYLine(x, conf.get('colour', 'grid-line-scroll')), next='scroll')

 # Function
 def plotFunctionLine(self, points, colour, lineWidth, fid):
  self.tagFunction(self.plotLine(*points, fill=colour, width=lineWidth), fid)
   
 # Labels
 def plotLabel(self, *args, **kwargs):
  return self.create_text(*args, **kwargs)
 
 def plotGridLabel(self, x, y, text='0'):
  return self.plotLabel(x + conf.get('gridpar', 'graphlabel-closer'),
   y - conf.get('gridpar', 'graphlabel-closer'), text=text, anchor=conf.get('gridpar', 'graphlabel-anchor'))
 
 # Grid Labels
 def plotXGridLabel(self, x, text):
  self.tagGrid(self.plotGridLabel(x=x, y=comp.getYAxis(), text=text), add='label-x')
 
 def plotYGridLabel(self, y, text): 
  self.tagGrid(self.plotGridLabel(x=comp.getXAxis(), y=y, text=text), add='label-y')

 # Dead Zones
 def plotRect(self, *args, **kwargs):
  return self.create_rectangle(*args, **kwargs)
  
 def plotHDeadZoneRect(self, y1, y2):
  self.tagDeadZone(self.plotRect(0, y1, comp.getWVal(), y2, fill=conf.get('colour', 'dead-zone'), width=0))
 
 def plotWDeadZoneRect(self, x1, x2):
  self.tagDeadZone(self.plotRect(x1, 0, x2, comp.getHVal(), fill=conf.get('colour', 'dead-zone'), width=0))
 
 def plotHDeadZoneLine(self):
  self.tagDeadZone(self.plotXLine(comp.getYAxis(), conf.get('colour', 'grid-line-4')))

 def plotWDeadZoneLine(self):
  self.tagDeadZone(self.plotYLine(comp.getXAxis(), conf.get('colour', 'grid-line-4')))
 
 def plotZeroLabel(self):
  self.tagDeadZone(self.plotGridLabel(x=comp.getXAxis(), y=comp.getYAxis(), text='0'))
 
 # Gettery jádra
 def getCanvasWidth(self):
  return int(self.cget('width'))
 
 def getCanvasHeight(self):
  return int(self.cget('height'))

    
class Panel(OutputClass, tk.Frame):
 def __init__(self, master):
  self.master = master
  tk.Frame.__init__(self, self.master)
  self.setVars()
  self.build()
  self.bindEvents()
 
 def build(self):
  pass
 
 def bindEvents(self):
  pass
 
 def setVars(self):
  pass
 
 def display(self):
  self.pack()
 

class ControlPanel(Panel):
 def build(self):
  self.topPanel = tk.Frame(self)
  self.middlePanel = tk.Frame(self)
  self.bottomPanel = tk.Frame(self)
  self.funcList = FunctionList(self.topPanel)
  self.zoomPanel = ZoomPanel(self.middlePanel)
  self.motionPanel = MotionPanel(self.middlePanel)
  self.funcPanel = FunctionPanel(self.bottomPanel) 

 def zoomNormalize(self):
  self.zoomPanel.zoomNormalize()

 def motion(self, *args, **kwargs):
  self.motionPanel.motion(*args, **kwargs)

 def motionEnd(self):
  self.motionPanel.motionEnd()

 def scrollStart(self, *args, **kwargs):
  self.motionPanel.scrollStart(*args, **kwargs)

 def scrollEnd(self, *args, **kwargs):
  self.motionPanel.scrollEnd(*args, **kwargs)
 
 def setXScale(self, value):
  self.zoomPanel.setXScale(value)
 
 def setXPiScale(self, quot):
  self.zoomPanel.setXPiScale(quot)
 
 def setYScale(self, value):
  self.zoomPanel.setYScale(value)

 def selectFunction(self, fid):
  self.unselectFunction(hide=False)
  self.funcList.selectFunction(fid)
  self.funcPanel.showEditPanels(fid)
 
 def unselectFunction(self, hide=True):
  selected = self.funcList.getSelectedIndex()
  if selected is not None:
   self.funcList.unselectFunction()
   if hide:
    self.funcPanel.hideEditPanels()
 
 def addFunction(self, fid, *args):
  self.funcList.addFunction(fid, *args)
  if fman.getFunction(fid).isParametric():
   self.funcPanel.registerFunction(fid)
 
 def updateFunction(self, fid, *args):
  self.funcList.updateFunction(fid, *args)
  if fman.getFunction(fid).isParametric():
   self.funcPanel.unregisterFunction(fid)
   self.funcPanel.registerFunction(fid)
 
 def createFunction(self, text):
  mgr.createFunction(text)
 
 def editFunction(self, text):
  mgr.editFunction(self.funcList.getSelectedFID(), text)
 
 def getExprEdit(self):
  return fman.getExprEdit(self.funcList.getSelectedFID())
 
 def deleteFunction(self):
  selected = self.funcList.getSelectedIndex()
  if selected is not None:
   mgr.deleteFunction(self.funcList.getSelectedFID())
 
 def removeFunction(self, fid):
  self.funcList.deleteFunction(fid)
  self.funcPanel.unregisterFunction(fid)
  self.funcPanel.hideEditPanels()
 
 def deleteAllFunctions(self):
  mgr.deleteAllFunctions()
 
 def display(self):
  self.pack(fill='y', expand=1)
  self.topPanel.pack(side='top', fill='x')
  self.middlePanel.pack(side='top', fill='x')
  self.bottomPanel.pack(side='top', fill='both', expand=1)
  self.funcList.display()
  self.zoomPanel.display()
  self.motionPanel.display()
  self.funcPanel.display()
 


class FunctionList(Panel):
 def __init__(self, master):
  Panel.__init__(self, master)
  self.fidList = []

 def itemSelected(self, event):
  self.after(20, self.functionSelected) # musi se chvili pockat, nez se zmeni vybrana polozka
 
 def itemUnselected(self, event):
  self.functionUnselected()
 
 def functionSelected(self, *args):
  selected = self.getSelectedFID()
  if selected is not None:
   mgr.selectFunction(selected)
 
 def functionUnselected(self):
  mgr.unselectFunction()
 
 def selectFunction(self, fid):
  self.funcList.selection_set(self.fidList.index(fid))
 
 def unselectFunction(self):
  self.funcList.selection_clear(self.getSelectedIndex())

 def addFunction(self, fid):
  self.insertFunction(fid, 'end')
 
 def updateFunction(self, fid):
  index = self.fidList.index(fid)
  self.removeFunction(index)
  self.insertFunction(fid, index)
  
 def insertFunction(self, fid, index):
  func = fman.getFunction(fid)
  if index == 'end':
   self.fidList.append(func.getFID())
  else:
   self.fidList.insert(index, func.getFID())
  self.funcList.insert(index, ('  ' + str(func.getNumber())).ljust(10) + func.getExpr())
 
 # Vymazava funkci uplne (externi vrstva, funkce mizi odevsad)
 def deleteFunction(self, fid):
  ford = self.fidList.index(fid)
  self.removeFunction(ford)
 
 # Vymazava funkci ze seznamu (interni vrstva)
 def removeFunction(self, index):
  self.funcList.delete(index)
  del self.fidList[index]
  
 def getSelectedIndex(self):
  selection = self.funcList.curselection()
  if not selection:
   return None
  else:
   return int(selection[0])

 def getSelectedFID(self):
  if self.getSelectedIndex() is not None:
   return self.fidList[self.getSelectedIndex()]
  else:
   fmanFID = fman.getSelectedFID()
   if fmanFID is not None:
    return fmanFID
   else:
    return None

 def build(self):
  self.frame = tk.LabelFrame(self, text=conf.get('out', 'funclist-header'))
  self.funcList = tk.Listbox(self.frame, height=conf.get('graphpar', 'funclist-lines'),
   width=conf.get('graphpar', 'funclist-width'), selectmode='single')

 def bindEvents(self):
  self.funcList.bind('<ButtonRelease-1>', self.itemSelected)
  self.funcList.bind('<ButtonRelease-3>', self.itemUnselected)
 
 def display(self):
  self.pack(side='top', fill='x')
  self.frame.pack(side='top', pady=2)
  self.funcList.pack(side='top', fill='x', padx=2, pady=2)



class ZoomPanel(Panel):
 def __init__(self, master):
  Panel.__init__(self, master)
  self.supBoth = False
  self.supX = False
 
 def setVars(self):
  self.bothVal = tk.StringVar()
  self.xVal = tk.StringVar()
  self.yVal = tk.StringVar()
  self.setAllVals(String.floatStr(conf.get('gridpar', 'default-scale')))

 def setAllVals(self, value):
  self.bothVal.set(value)
  self.xVal.set(value)
  self.yVal.set(value)


 # ZOOM PANEL METHODS

 def zoomBoth(self, event=None):
  bothText = self.bothVal.get()
  try:
   zoomBoth = base.parseFloat(bothText)
  except ValueError:
   if self.supBoth:
    self.bothVal.set('')
   else:
    self.bothVal.set(plot.getXScale())
   return
  mgr.setBothScales(zoomBoth)
  self.supBoth = False
  disp = String.floatStr(zoomBoth)
  self.bothVal.set(disp)
  self.xVal.set(disp)
  self.xVal.set(disp)
  
 def zoomX(self, event=None):
  xText = self.xVal.get()
  try:
   zoomX = base.parseFloat(xText)
  except ValueError:
   self.xVal.set(plot.getXScale())
   return
  self.setXScale(zoomX)

 def zoomY(self, event=None):
  yText = self.yVal.get()
  try:
   zoomY = base.parseFloat(yText)
  except ValueError:
   self.yVal.set(plot.getYScale())
   return
  self.setYScale(zoomY)
 
 def zoomBothOut(self, *args):
  mgr.zoomBothOut()
  print(self.supBoth)
  if not self.supBoth:
   self.zoomBothMult()
  self.zoomXMult()
  self.zoomYMult()
 
 def zoomBothIn(self, *args):
  mgr.zoomBothIn()
  if not self.supBoth:
   self.zoomBothDiv()
  self.zoomXDiv()
  self.zoomYDiv()

 def zoomXOut(self):
  mgr.zoomXOut()
  self.zoomXMult()
  self.suppressBoth()
 
 def zoomXIn(self):
  mgr.zoomXIn()
  self.zoomXDiv()
  self.suppressBoth()

 def zoomYOut(self):
  mgr.zoomYOut()
  self.zoomYMult()
  self.suppressBoth()
 
 def zoomYIn(self):
  mgr.zoomYIn()
  self.zoomYDiv()
  self.suppressBoth()
 
 def zoomNormalized(self):
  mgr.zoomNormalize()
 
 def zoomNormalize(self):
  disp = String.floatStr(conf.get('gridpar', 'default-scale'))
  self.setAllVals(disp)
 
 def zoomXPi(self, *args):
  self.setXPiScale(self.xPiMultVar.get())
 
 def setXScale(self, value):
  mgr.setXScale(base.parseFloat(value))
  self.suppressBoth()
  self.xVal.set(String.floatStr(value))
 
 def setXPiScale(self, mult):
  mgr.setXPiScale(mult)
  self.suppressX()
  
 def setYScale(self, value):
  mgr.setYScale(base.parseFloat(value))
  self.suppressBoth()
  self.yVal.set(String.floatStr(value))

 def suppressBoth(self):
  if not self.supBoth:
   self.bothVal.set('')
   self.supBoth = True
 
 def suppressX(self):
  if not self.supX:
   self.bothVal.set('')
   self.supX = True
 
 def zoomBothMult(self):
  self.bothVal.set(String.floatStr(base.parseFloat(self.bothVal.get()) * conf.get('gridpar', 'scale-multiplier'))) 
 
 def zoomBothDiv(self):
  self.bothVal.set(String.floatStr(base.parseFloat(self.bothVal.get()) / conf.get('gridpar', 'scale-multiplier'))) 

 def zoomXMult(self):
  baseVal = self.xVal.get()
  if not baseVal:
   baseVal = comp.getXScale()
  self.xVal.set(String.floatStr(base.parseFloat(baseVal) * conf.get('gridpar', 'scale-multiplier')))
  self.supX = False
  
 def zoomXDiv(self):
  baseVal = self.xVal.get()
  if not baseVal:
   baseVal = comp.getXScale()
  self.xVal.set(String.floatStr(base.parseFloat(baseVal) / conf.get('gridpar', 'scale-multiplier')))
  self.supX = False

 def zoomYMult(self):
  self.yVal.set(String.floatStr(base.parseFloat(self.yVal.get()) * conf.get('gridpar', 'scale-multiplier')))
  
 def zoomYDiv(self):
  self.yVal.set(String.floatStr(base.parseFloat(self.yVal.get()) / conf.get('gridpar', 'scale-multiplier')))


 def build(self):
  # Panel a hlavicka
  self.mainPanel = tk.LabelFrame(self, text=conf.get('out', 'zoompanel-header'))
  self.bodyPanel = tk.Frame(self.mainPanel)
  self.labelPanel = tk.Frame(self.bodyPanel)
  self.widgetPanel = tk.Frame(self.bodyPanel)
  self.xPiPanel = tk.Frame(self.mainPanel)
  # Popisky kategorii
  self.bothLabel = tk.Label(self.labelPanel, text=conf.get('out', 'zoompanel-both'))
  self.xLabel = tk.Label(self.labelPanel, text=conf.get('out', 'zoompanel-x'))
  self.yLabel = tk.Label(self.labelPanel, text=conf.get('out', 'zoompanel-y'))
  # Celkovy zoom
  self.bothPanel = tk.Frame(self.widgetPanel)
  self.bothPlus = tk.Button(self.bothPanel, image=win.plusImg, command=self.zoomBothIn)
  self.bothMinus = tk.Button(self.bothPanel, image=win.minusImg, command=self.zoomBothOut)
  self.bothEntry = tk.Entry(self.bothPanel, justify='right', width=6, exportselection=0, textvariable=self.bothVal)
  # X-zoom
  self.xPanel = tk.Frame(self.widgetPanel)
  self.xPlus = tk.Button(self.xPanel, image=win.plusImg, command=self.zoomXIn)
  self.xMinus = tk.Button(self.xPanel, image=win.minusImg, command=self.zoomXOut)
  self.xEntry = tk.Entry(self.xPanel, justify='right', width=6, exportselection=0, textvariable=self.xVal)
  # Y-zoom
  self.yPanel = tk.Frame(self.widgetPanel)
  self.yPlus = tk.Button(self.yPanel, image=win.plusImg, command=self.zoomYIn)
  self.yMinus = tk.Button(self.yPanel, image=win.minusImg, command=self.zoomYOut)
  self.yEntry = tk.Entry(self.yPanel, justify='right', width=6, exportselection=0, textvariable=self.yVal)
  # Pomocna tlacitka
  self.normalButton = tk.Button(self.xPiPanel, image=win.oneImg, command=self.zoomNormalized)
  self.xPiButton = tk.Button(self.xPiPanel, image=win.piImg, command=self.zoomXPi)
  self.xPiMultVar = tk.IntVar()
  self.xPiMultVar.set(1)
  self.xPiMultEntry = tk.Entry(self.xPiPanel, justify='right', width=4, exportselection=0, textvariable=self.xPiMultVar)

 def bindEvents(self):
  self.bothEntry.bind('<KeyRelease-Return>', self.zoomBoth)
  self.xEntry.bind('<KeyRelease-Return>', self.zoomX)
  self.yEntry.bind('<KeyRelease-Return>', self.zoomY)
  self.xPiMultEntry.bind('<KeyRelease-Return>', self.zoomXPi)
  
 def display(self):
  self.pack(side='left', padx=2)
  self.mainPanel.pack(side='top')
  self.bodyPanel.pack(side='top')
  self.labelPanel.pack(side='left', fill='y', expand=1)
  self.widgetPanel.pack(side='left', fill='y', expand=1)
  self.xPiPanel.pack(side='top', fill='x', expand=1, padx=2, pady=2)
  # Popisky
  self.bothLabel.pack(side='top', fill='x', expand=1)
  self.xLabel.pack(side='top', fill='x', expand=1)
  self.yLabel.pack(side='top', fill='x', expand=1)  
  # Celkovy zoom
  self.bothPanel.pack(side='top', fill='x', expand=1)
  self.bothPlus.pack(side='left')
  self.bothMinus.pack(side='left')
  self.bothEntry.pack(side='left', padx=2)
  # X-zoom
  self.xPanel.pack(side='top', fill='x', expand=1)
  self.xPlus.pack(side='left')
  self.xMinus.pack(side='left')
  self.xEntry.pack(side='left', padx=2)
  # Y-zoom
  self.yPanel.pack(side='top', fill='x', expand=1)
  self.yPlus.pack(side='left')
  self.yMinus.pack(side='left')
  self.yEntry.pack(side='left', padx=2)
  # Pomocna tlacitka
  self.normalButton.pack(side='left')  
  self.xPiButton.pack(side='left')
  self.xPiMultEntry.pack(side='left')
  # self.xPi4Button.pack(side='left')
  # self.xPi6Button.pack(side='left')
  # self.xPi12Button.pack(side='left')



class MotionPanel(Panel):
 def motion(self, x, y, scroll):
  self.xLabel.config(text=('x: ' + (conf.get('out', 'position-format').format(float(x)))))
  self.yLabel.config(text=('y: ' + (conf.get('out', 'position-format').format(float(y)))))
  if scroll:
   self.scrollModify(x, y)
   
 def motionEnd(self):
  self.xLabel.config(text='')
  self.yLabel.config(text='')
 
 def scrollStart(self, x, y):
  self.scrollBegin = (x, y)
  self.scrollModify(x, y)
 
 def scrollModify(self, x, y):
  self.scrollActual = (x, y)
  self.scrollChange = (x - self.scrollBegin[0], y - self.scrollBegin[1])
  self.xLabel.config(text=('dx: ' + (conf.get('out', 'position-format').format(self.scrollChange[0]))))
  self.yLabel.config(text=('dy: ' + (conf.get('out', 'position-format').format(self.scrollChange[1]))))
 
 def scrollEnd(self):
  self.xLabel.config(text='')
  self.yLabel.config(text='')
 
 def scrollCenter(self):
  mgr.scrollCenter()
 
 def scrollEdge(self):
  mgr.scrollEdge()

 def scrollBottom(self):
  mgr.scrollBottom()

 def scrollCorner(self):
  mgr.scrollCorner()
  
 def switchLines(self):
  mgr.switchMotionLines()


 def build(self):
  self.frame = tk.LabelFrame(self, text=conf.get('out', 'motion-header'))
  self.linesCheck = tk.Checkbutton(self.frame, text=conf.get('out', 'motion-lines-checker'), command=self.switchLines)
  self.posPanel = tk.Frame(self.frame)
  self.xLabel = tk.Label(self.posPanel, text='')
  self.yLabel = tk.Label(self.posPanel, text='')
  self.footerPanel = tk.Frame(self.frame)
  # defined scroll buttons
  self.centerButton = tk.Button(self.footerPanel, image=win.centerImg, command=self.scrollCenter)
  self.edgeButton = tk.Button(self.footerPanel, image=win.edgeImg, command=self.scrollEdge)
  self.bottomButton = tk.Button(self.footerPanel, image=win.bottomImg, command=self.scrollBottom)
  self.cornerButton = tk.Button(self.footerPanel, image=win.cornerImg, command=self.scrollCorner)

 def display(self):
  self.pack(side='left', fill='both', expand=1, padx=4)
  self.frame.pack(side='top', pady=2)
  self.linesCheck.pack(side='top')
  self.posPanel.pack(side='top', fill='both', expand=1)
  self.xLabel.pack(side='top', pady=2)
  self.yLabel.pack(side='top', pady=2)
  self.footerPanel.pack(side='bottom', fill='x', expand=1, padx=5)
  self.centerButton.pack(side='right')
  self.bottomButton.pack(side='right')
  self.edgeButton.pack(side='right')
  self.cornerButton.pack(side='right')
 
 

class FunctionPanel(Panel):
 def build(self):
  self.frame = tk.LabelFrame(self, text=conf.get('out', 'funcpanel-header'))
  self.mainPanel = tk.Frame(self.frame)
  self.exprPanel = FunctionExprPanel(self.mainPanel)
  self.managePanel = FunctionManagePanel(self.mainPanel)
 
 def display(self):
  self.pack(side='top', fill='both', expand=1, padx=2, pady=5)
  self.frame.pack(side='top', fill='both', expand=1)
  self.mainPanel.pack(side='top', fill='both', expand=1, padx=2, pady=2)
  self.exprPanel.display()
  self.managePanel.display()
 
 def registerFunction(self, fid):
  self.managePanel.registerFunction(fid)
 
 def unregisterFunction(self, fid):
  self.managePanel.unregisterFunction(fid)
 
 def showEditPanels(self, fid=None):
  self.exprPanel.showEditButton()
  self.managePanel.showMain(fid)
 
 def hideEditPanels(self):
  self.exprPanel.hideEditButton()
  self.managePanel.hideMain()
 

class FunctionExprPanel(Panel):
 def __init__(self, *args, **kwargs):
  Panel.__init__(self, *args, **kwargs)
  self.state = None
  self.headers = {'add' : conf.get('out', 'funcpanel-add-header'), 'edit' : conf.get('out', 'funcpanel-edit-header')}
  self.confirms = {'add' : conf.get('out', 'funcpanel-add-confirm'), 'edit' : conf.get('out', 'funcpanel-edit-confirm')}
 
 def build(self):
  self.initPanel = tk.Frame(self)
  self.addButton = tk.Button(self.initPanel, text=conf.get('out', 'funcpanel-add-button'), command=self.addMain, width=12)
  self.editButton = tk.Button(self.initPanel, text=conf.get('out', 'funcpanel-edit-button'), command=self.editMain, width=12)
  self.mainPanel = tk.Frame(self)
  self.row1Panel = tk.Frame(self.mainPanel)
  self.row2Panel = tk.Frame(self.mainPanel)
  self.header = tk.Label(self.row1Panel, text='')
  self.label = tk.Label(self.row2Panel, text='y = ')
  self.entry = tk.Entry(self.row2Panel, width=35, textvariable=self.entryVar)
  self.cancel = tk.Button(self.row1Panel, text=conf.get('out', 'cancel'), command=self.hideMain)
  self.confirm = tk.Button(self.row1Panel, text='', command=self.submit)

 def bindEvents(self):
  self.entry.bind('<KeyRelease>', self.checkExpr)
  self.entry.bind('<KeyRelease-Return>', self.submit)
 
 def setVars(self):
  self.entryVar = tk.StringVar()

 def display(self):
  self.pack(side='top', fill='x')
  self.showInitPanel()
 
 def addMain(self, event=None):
  self.state = 'add'
  self.showMain()
  
 def editMain(self, event=None):
  self.state = 'edit'
  self.entryVar.set(panel.getExprEdit())
  self.showMain()
  
 def showMain(self):
  self.hideInitPanel()
  self.mainPanel.pack(side='top', pady=2)
  self.row1Panel.pack(side='top', fill='x', expand=1)
  self.header.config(text=self.headers[self.state])
  self.header.pack(side='left')
  self.confirm.config(text=self.confirms[self.state])
  self.confirm.pack(side='right')
  self.cancel.pack(side='right')
  self.row2Panel.pack(side='top', fill='x', expand=1)
  self.label.pack(side='left')
  self.entry.pack(side='right', fill='x', expand=1)
  self.entry.focus_set()

 def showInitPanel(self):
  self.initPanel.pack(side='top', fill='x')
  self.addButton.pack(side='left')
 
 def hideInitPanel(self):
  self.initPanel.pack_forget()

 def showEditButton(self):
  self.editButton.pack(side='right')
 
 def hideEditButton(self):
  self.editButton.pack_forget()

 def hideMain(self, event=None):
  self.entryVar.set('')
  self.mainPanel.pack_forget()
  self.showInitPanel()

 def checkExpr(self, event=None):
  pass
 
 def submit(self, event=None):
  entryText = self.entryVar.get()
  if entryText:
   if self.state == 'add':
    panel.createFunction(entryText)
   elif self.state == 'edit':
    panel.editFunction(entryText)
   self.hideMain()


class FunctionManagePanel(Panel):
 def __init__(self, master, fid=None):
  Panel.__init__(self, master)
  self.paramSetters = {}
  self.panels = {}
  if fid:
   self.loadFunction(fid)

 def registerFunction(self, fid):
  func = fman.getFunction(fid)
  self.paramSetters[fid] = {}
  self.panels[fid] = tk.LabelFrame(self.paramPanel, text='Funkce {expr} ({num:d})'.format(expr=func.getExpr(), num=func.getNumber()))
  self.panels[fid].pack(side='top', fill='x')
  for par in func.getPars():
   self.paramSetters[fid][par] = FunctionParameterSetter(self.panels[fid], fid, par)
   self.paramSetters[fid][par].display()
 
 def unregisterFunction(self, fid):
  if fid in self.panels:
   self.panels[fid].pack_forget()
   del self.paramSetters[fid]
 
 def chooseColor(self):
  mgr.changeFuncColor(color=tkcolc.askcolor(title=conf.get('out', 'funcpanel-colorchoose'))[1])
 
 def deleteFunction(self):
  panel.deleteFunction()
 
 def deleteAllFunctions(self):
  panel.deleteAllFunctions()

 def showMain(self, fid=None):
  self.propertyPanel.pack(side='bottom', fill='x', pady=5)
  self.colorChooseButton.pack(side='left')
  self.removeButton.pack(side='left')
 
 def hideMain(self):
  self.propertyPanel.pack_forget()
  self.removeButton.pack_forget()
 
 def build(self):
  self.paramPanel = tk.Frame(self)
  self.propertyPanel = tk.Frame(self)
  self.colorChooseButton = tk.Button(self.propertyPanel, text=conf.get('out', 'funcpanel-colorchoose'), command=self.chooseColor, width=12)
  self.removePanel = tk.Frame(self)
  self.removeButton = tk.Button(self.removePanel, text=conf.get('out', 'funcpanel-remove'), command=self.deleteFunction, width=12)
  self.removeAllButton = tk.Button(self.removePanel, text=conf.get('out', 'funcpanel-removeall'), command=self.deleteAllFunctions, width=12)

 def display(self):
  self.pack(side='top', fill='both', expand=1)
  self.paramPanel.pack(side='top', fill='x', pady=10)
  self.removePanel.pack(side='bottom', fill='x')
  self.removeAllButton.pack(side='right')



class FunctionParameterSetter(Panel):
 def __init__(self, master, fid, par):
  self.function = fman.getFunction(fid)
  self.par = par
  Panel.__init__(self, master)
 
 def setVars(self):
  self.entryVar = tk.StringVar()
  self.stepVar = tk.StringVar()
  self.entryVar.set(String.floatStr(self.function.getParValue(self.par)))
  self.stepVar.set(String.floatStr(conf.get('gridpar', 'par-default-step')))
 
 def valueChanged(self, event):
  newVal = base.parseFloat(self.entryVar.get())
  self.function.setParValue(self.par, newVal)
 
 def valueModify(self, modif):
  newVal = base.parseFloat(self.entryVar.get()) + modif
  self.entryVar.set(String.floatStr(newVal))
  self.function.setParValue(self.par, newVal)
 
 def valueUp(self):
  self.valueModify(base.parseFloat(self.stepVar.get()))
  
 def valueDown(self):
  self.valueModify(-base.parseFloat(self.stepVar.get()))
   
 def build(self):
  self.row1Panel = tk.Frame(self)
  self.label = tk.Label(self.row1Panel, text=(self.par + ' = '))
  self.valueEntry = tk.Entry(self.row1Panel, width=6, textvariable=self.entryVar)
  self.row2Panel = tk.Frame(self)
  self.plusButton = tk.Button(self.row2Panel, image=win.plusImg, repeatdelay=500, repeatinterval=30, command=self.valueUp)
  self.minusButton = tk.Button(self.row2Panel, image=win.minusImg, repeatdelay=500, repeatinterval=30, command=self.valueDown)
  self.stepEntry = tk.Entry(self.row2Panel, width=3, textvariable=self.stepVar)
 
 def bindEvents(self):
  self.valueEntry.bind('<KeyRelease-Return>', self.valueChanged)
 
 def display(self):
  self.pack(side='left', padx=5)
  self.row1Panel.pack(side='top', fill='x')
  self.label.pack(side='left')
  self.valueEntry.pack(side='left')
  self.row2Panel.pack(side='top', fill='x')
  self.plusButton.pack(side='left')
  self.minusButton.pack(side='left')
  self.stepEntry.pack(side='left')
  


class MainMenu(OutputClass, tk.Menu):
 def __init__(self, master, confFile=None):
  mainWin = master.winfo_toplevel()
  tk.Menu.__init__(self, mainWin)
  mainWin['menu'] = self
  self.menus = {}
  self.menuKeys = []
  self.initMenus(cf=self.loadMenuConfig(confFile))
 
 def loadMenuConfig(self, menuFile=None):
  if not menuFile:
   self.menuFileName = 'fcink-menu'
   self.menuFilePath = self.menuFileName + '.xml'
   return ioc.XMLReader(self.menuFilePath, encoding='utf8')
  else:
   return menuFile
  
 def initMenus(self, cf):
  root = cf.child(cf.getRoot(), 'mainmenu')
  for primCasc in cf.children(root, 'cascade'):
   self.addCascade(self, cf, primCasc)
 
 def addCascade(self, master, cf, cascade):
  menu = MenuCascade(master, cf.attrib(cascade, 'name'), cf.attrib(cascade, 'desc'))
  for elem in cf.children(cascade):
   if cf.tagName(elem) == 'command':
    self.addCommand(menu, cf.attrib(elem, 'name'), cf.attrib(elem, 'command'), cf.attrib(elem, 'desc'))
   if cf.tagName(elem) == 'separator':
    self.addSeparator(menu)
   if cf.tagName(elem) == 'cascade':
    self.addCascade(menu, cf, elem)
  
 def addCommand(self, master, label, command, hint=None, shortcut=None):
  MenuCommand(master, label, command, hint, shortcut)
 
 def addSeparator(self, menu):
  menu.addSeparator()
  
 def display(self):
  pass


class MenuCascade(OutputClass, tk.Menu):
 def __init__(self, master, label, hint=None):
  self.master = master
  self.label = label
  tk.Menu.__init__(self, self.master, tearoff=False)
  self.create()
 
 def create(self):
  self.master.add_cascade(label=self.label, menu=self)
 
 def addSeparator(self):
  self.add_separator()
  

class MenuCommand(OutputClass):
 def __init__(self, master, label, command, hint=None, shortcut=None):
  self.master = master
  self.label = label
  exec('self.command = ' + command)
  self.create()
 
 def create(self):
  self.master.add_command(label=self.label, command=self.command)
  

# class MainMenu(OutputClass, tk.Frame):
#  def __init__(self, master):
#   tk.Frame.__init__(self, master)
#   self.menus = {}
#   self.menuKeys = []
#   self.initMenus()
# 
#  def initMenus(self):
#   self.addMenu('FILE', 'Soubor', 'Práce se soubory projektů, export')
#   self.addMenuItem('FILE', 'Otevřít', mgr.openCommand)
#   self.addMenuItem('FILE', 'Uložit', mgr.saveCommand)
#   self.addMenuItem('FILE', 'Uložit jako', mgr.saveAsCommand)
#   self.addMenuItem('FILE', 'Konec', main.exit)
#   self.addMenu('GRID', 'Mřížka', 'Manipulace s mřížkou a osami grafu')
#   self.addMenuItem('GRID', 'Vystřeď', panel.scrollCenter)
#   self.addMenuItem('GRID', 'Ortonormální', panel.zoomNormalized)
#   self.addMenuItem('GRID', 'Normalizuj', self.normalizeGrid)
#  
#  def addMenu(self, key, text='Menu', statusHint=None):
#   self.menuKeys.append(key)
#   self.menus[key] = tk.Menubutton(self, text=text)
#   self.menus[key].menu = tk.Menu(self.menus[key], tearoff=0)
#   self.menus[key]['menu'] = self.menus[key].menu
#   if statusHint is None: statusHint = text
#   self.menus[key].statusHint = statusHint
#   self.menus[key].bind('<Enter>', self.showStatusHint)
#   self.menus[key].bind('<Leave>', self.hideStatusHint)
#  def addMenuItem(self, menuKey, label, command):
#   self.menus[menuKey].menu.add_command(label=label, command=command)
#   # self.menus[menuKey].menu.
#   # TODO: ještě zkusit někde vyhrabat, jak by šla status hint i pro položky menu
 
#  def display(self):
#   self.pack(side='left', fill='both', expand=1)
#   for key in self.menuKeys:
#    self.menus[key].pack(side='left', anchor='nw')
# 
#  def showStatusHint(self, event):
#   win.status.change(event.widget.statusHint) # zobrazuje ve statusbaru text nápovědy pro položku menu
 
#  def hideStatusHint(self, event):
#   win.status.rollback() # vrací původní text
#  

 

# class StatusBar(OutputClass, tk.Label):
#  def __init__(self, master, defText=''):
#   self.default = str(defText)
#   self.current = str(defText)
#   tk.Label.__init__(self, master, text=self.default)
#  
#  def change(self, text=''):
#   self.current = text
#   self.config(text=self.current)
#  
#  def rollback(self):
#   self.config(text=self.default)
#  
#  def display(self):
#   self.pack(side='left')
 
class SupportClass(BaseClass):
 pass

class FileWorkClass(SupportClass):
 pass
 
class Config(FileWorkClass):
 def __init__(self, confFileName=None):
  self.confFileName = confFileName or 'fcink-conf'
  self.confFilePath = self.confFileName + '.xml'
  self.confFile = ioc.XMLReader(self.confFilePath, encoding='utf8')
  self.confDict = self.confFile.getBaseConfDict(('proginfo', 'paths', 'outs', 'colours', 'gridpars', 'graphpars'))
  self.confFile.close()
  self.funcColours = 0
  for key in self.confDict['colour'].keys():
   if 'function' in key:
    self.funcColours += 1
 
 def getFuncColour(self, i):
  return self.get('colour', 'function-' + str(i % self.funcColours))
 
 def get(self, sectName, key=None):
  try:
   sect = self.confDict[sectName]
  except KeyError:
   raise KeyError(sectName + ' section not found')
  if key is None: return sect
  try:
   return sect[key]
  except KeyError:
   raise KeyError(key + ' not found in section ' + sectName)
 
 def getPi(self):
  return math.pi
   
   
   
class Logger(FileWorkClass):
 def __init__(self, fname=None):
  if fname is None:
   self.fileName = Date.fileDate() + '-log.log'
  else:
   self.fileName = fname
  self.log = ioc.LogWriter(os.path.join(conf.get('path', 'log'), self.fileName), mode='a', encoding='utf8')
  self.log.header(progName=conf.get('proginfo', 'program'), progAuthor=conf.get('proginfo', 'author'),
   progVersion=conf.get('proginfo', 'version'))
 
 def logMisc(self, info):
  self.log.writeTimed(info)
 
 def logNamed(self, name, info):
  self.log.writeTimed('{name} - {info}'.format(name=name, info=info))



class DataOperator(FileWorkClass):
 def __init__(self, fileName=None, filePath=None):
  if fileName is not None:
   self.fileName = fileName
   self.filePath = self.getFilePath(self.fileName)
  else:
   self.filePath = filePath
   self.fileName = self.getFileName(self.filePath)

 def getFileName(self, filePath):
  return os.path.split(filePath)[1].split('.')[0]

 def getFilePath(self, fileName):
  return os.path.join(conf.get('path', 'data'), self.fileName + '.' + DATAF_EXT)


class Importer(DataOperator):
 def load(self):
  self.data = ioc.XMLReader(self.filePath)
  root = self.data.getRoot()
  gridData = self.data.child(root, 'gridinfo')
  self.wFactor = float(self.data.childContent(gridData, 'wfactor'))
  self.hFactor = float(self.data.childContent(gridData, 'hfactor'))
  self.xScale = float(self.data.childContent(gridData, 'xscale'))
  self.yScale = float(self.data.childContent(gridData, 'yscale'))
  if self.data.child(gridData, 'xpiquot'):
   self.xPiQuot = int(self.data.childContent(gridData, 'xpiquot'))
  else:
   self.xPiQuot = 0
  funcData = self.data.child(root, 'funcinfo')
  funcList = self.data.children(funcData, 'function')
  self.functions = {}
  for funcEl in funcList:
   self.functions[int(self.data.attribute(funcEl, 'id'))] = (int(self.data.attribute(funcEl, 'ord')),
     self.data.childContent(funcEl, 'exprsrc'), self.data.childContent(funcEl, 'exprfin'))
 
 def getWFactor(self):
  return self.wFactor
 
 def getHFactor(self):
  return self.hFactor
 
 def getXScale(self):
  return self.xScale
 
 def getYScale(self):
  return self.yScale
 
 def getXPiQuot(self):
  return self.xPiQuot
 
 def getFunctionList(self):
  return self.functions


class Exporter(DataOperator):
 def save(self):
  self.file = ioc.XMLWriter(self.filePath)
  self.file.createRoot('graphdata', {'name' : self.fileName, 'type' : 'misc'})
  self.file.element(elName='gridinfo')
  self.file.element(position=[0], elName='wfactor', elVal=comp.getWFactor())
  self.file.element(position=[0], elName='hfactor', elVal=comp.getHFactor())
  self.file.element(position=[0], elName='xscale', elVal=comp.getXScale())
  self.file.element(position=[0], elName='yscale', elVal=comp.getYScale())
  self.file.element(position=[0], elName='xpiquot', elVal=int(comp.getXPiQuot()))
  self.file.element(elName='funcinfo')
  for fid in fman.getFunctionIds():
   func = fman.getFunction(fid)
   self.file.element(position=[1], elName='function', elAttrib={'id' : str(fid), 'ord' : str(func.getNumber())})
   self.file.element(position=[1, -1], elName='exprsrc', elVal=func.getExpr())
   self.file.element(position=[1, -1], elName='exprfin', elVal=func.getExprFin())
  self.file.write()
 

class ErrorHandler(BaseClass):
 def __init__(self, infOut=sys.stdout, logOut=sys.stdout):
  self.setLogOut(logOut)
  self.setInfOut(infOut)
 
 def setLogOut(self, logOut):
  if issubclass(logOut.__class__, ioc.Writer): 
   self.logOut = logOut
  else:
   self.logOut = ioc.LogWriter(logOut, encoding='utf8')

 def setInfOut(self, infOut):
  if issubclass(infOut.__class__, ioc.Writer):
   self.infOut = infOut
  else:
   self.infOut = ioc.PrintWriter(infOut, encoding='utf8')

 def stdReset(self):
  self.setLogOut(log.log)
  self.setInfOut(sys.stdout)

 def handleMainError(self, error):
  self.handleError(error)
  sys.exit(1)
  
 def handleError(self, error):
  self.writeError(error)
  self.logError(error)
 
 def handleLoopError(self, errType, errValue, traceback):
  self.handleError(errValue)
  self.errorAlert(errValue)
 
 def errorAlert(self, error):
  ErrAlert(self.getExcDesc(error), self.logOut.getName())
 
 def writeError(self, error):
  self.infOut.writeln('ERROR - for description see {file}'.format(file=self.logOut.getName()))
 
 def logError(self, error):
  self.logOut.error(error)
 
 def getExcDesc(self, error):
  return base.getExcDesc(error)


class ErrAlert(OutputClass, tk.Toplevel):
 def __init__(self, excDesc, logName):
  tk.Toplevel.__init__(self)
  self.title(conf.get('out', 'error-alert-title'))
  self.frame = tk.Frame(self)
  self.frame.pack(side='top', fill='both', expand=1)
  self.header = tk.Label(self.frame, text=conf.get('out', 'error-alert-header'), font=conf.get('graphpar', 'bold-font'))
  self.header.pack(side='top', anchor='nw', padx=5, pady=5)
  tk.Label(self.frame, text=excDesc).pack(side='top', padx=15)
  tk.Label(self.frame, text=(conf.get('out', 'error-alert-debuginfo') + '  ' + logName)).pack(side='top', anchor='w', padx=5, pady=4)
  self.resizable(False, False)


if __name__ == '__main__':
 try:
  main = Processor()
  main.run()
 finally:
  sys.stderr.flush()

  