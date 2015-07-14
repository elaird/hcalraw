import utils
r = utils.ROOT()


class autoBook(dict):
    def __init__(self, arg=None):
        if type(arg) == str:
            self.__directory = r.TDirectory(arg, arg)
        elif arg:
            self.__directory = arg
        else:
            self.__directory = 0

        self.fillOrder = []
        self.weight = 1


    @property
    def title(self):
        return self.__directory.GetName() if self.__directory else ""


    def fillGraph(self, x, name, title=""):
        self.fill(x, name, None, None, None, title=title)


    def __book(self, is_tgraph, x, name, N, low, up, title, xAxisLabels, yAxisLabels):
        if True:
            self.__directory.cd()
            self.fillOrder.append(name)
            if is_tgraph:
                self[name] = r.TGraph()
                self[name].SetName(name)
                self[name].SetTitle(title)
            elif type(x) != tuple:
                self[name] = r.TH1D(name, title, N, low, up)
            elif type(N) != tuple:
                self[name] = r.TProfile(name, title, N, low, up)
            elif len(N) == 2:
                self[name] = r.TH2D(name, title,
                                    N[0], low[0], up[0],
                                    N[1], low[1], up[1])
            else:
                self[name] = r.TH3D(name, title,
                                    N[0], low[0], up[0],
                                    N[1], low[1], up[1],
                                    N[2], low[2], up[2])

            if (not is_tgraph) and not self[name].GetSumw2N():
                self[name].Sumw2()
            for i, label in enumerate(xAxisLabels):
                self[name].GetXaxis().SetBinLabel(i+1, label)
            for i, label in enumerate(yAxisLabels):
                self[name].GetYaxis().SetBinLabel(i+1, label)


    def fill(self, x, name, N, low, up, w=None,
             title="", xAxisLabels=[], yAxisLabels=[]):

        is_tgraph = N is None
        if name not in self:
            self.__book(is_tgraph, x, name, N, low, up, title, xAxisLabels, yAxisLabels)

        if w is None:
            w = self.weight

        if is_tgraph:
            self[name].SetPoint(self[name].GetN(), x[0], x[1])
        elif type(x) != tuple:
            self[name].Fill(x, w)
        elif len(N) == 2 or type(N) != tuple:
            self[name].Fill(x[0], x[1], w)
        else:
            self[name].Fill(x[0], x[1], x[2], w)
