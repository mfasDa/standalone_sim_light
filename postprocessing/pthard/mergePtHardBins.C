struct filedata {
    double nevents;
    double crosssection;
    TH1 *hKt;
    std::map<int, TH1 *> hSpectra;
    std::map<int, TH2 *> hZg ,hRg, hNsd, hThetag;
};

void prepareHist(TH1 *hist, double nevents) {
    hist->SetDirectory(nullptr);
    hist->Scale(1./nevents);
}

TH1 *merge(std::vector<TH1 *> histos) {
    TH1 *result(nullptr);
    for(auto h : histos) {
        if(!result) {
            result = static_cast<TH1 *>(h->Clone());
            result->SetDirectory(nullptr);
        } else {
            result->Add(h);
        }
    }
    return result;
}

std::vector<TH1 *> getMergeList(std::map<int, filedata> &files, std::string observable, int R) {
    std::vector<TH1 *> result;
    for(auto bin : files) {
        if(observable == "kt") result.push_back(bin.second.hKt);
        else if(observable == "spectrum") result.push_back(bin.second.hSpectra[R]);
        else if(observable == "zg") {
            auto found = bin.second.hZg.find(R);
            if(found != bin.second.hZg.end()) result.push_back(found->second);
        }
        else if(observable == "rg") {
            auto found = bin.second.hRg.find(R);
            if(found != bin.second.hRg.end()) result.push_back(found->second);
        }
        else if(observable == "nsd"){
            auto found = bin.second.hNsd.find(R);
            if(found != bin.second.hNsd.end()) result.push_back(found->second);
        } 
        else if(observable == "thetag") {
            auto found = bin.second.hThetag.find(R);
            if(found != bin.second.hThetag.end()) result.push_back(found->second);
        }
    }
    return result;
}

filedata readFile(const char *filename) {
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    filedata result;
    result.nevents = static_cast<TH1 *>(reader->Get("hNevents"))->GetBinContent(1);
    result.crosssection = static_cast<TH1 *>(reader->Get("hXsection"))->GetBinContent(1);
    result.hKt = static_cast<TH1 *>(reader->Get("hKtWeighted"));
    prepareHist(result.hKt, result.nevents);
    TH2 *dist(nullptr);
    for(auto R : ROOT::TSeqI(2, 7)) {
        reader->cd("Spectra");
        result.hSpectra[R] = static_cast<TH1 *>(gDirectory->Get(Form("JetSpectrumWeightedR%02d", R)));
        prepareHist(result.hSpectra[R], result.nevents);
        reader->cd("Zg");
        dist = static_cast<TH2 *>(gDirectory->Get(Form("hZgWeightR%02d", R)));
        if(dist) {
            prepareHist(dist, result.nevents);
            result.hZg[R] = dist;
        }
        reader->cd("Rg");
        dist = static_cast<TH2 *>(gDirectory->Get(Form("hRgWeightR%02d", R)));
        if(dist) {
            prepareHist(dist, result.nevents);
            result.hRg[R] = dist;
        }
        reader->cd("Nsd");
        dist = static_cast<TH2 *>(gDirectory->Get(Form("hNsdWeightR%02d", R)));
        if(dist) {
            prepareHist(dist, result.nevents);
            result.hNsd[R] = dist;
        }
        reader->cd("Thetag");
        dist = static_cast<TH2 *>(gDirectory->Get(Form("hThetagWeightR%02d", R)));
        if(dist) {
            prepareHist(dist, result.nevents);
            result.hThetag[R] = dist;
        }
    }
    return result;
}

void mergePtHardBins(){
    std::map<int, filedata> files;
    for(auto b : ROOT::TSeqI(0, 21)) {
        files[b] = readFile(Form("bin%d/jetspectrum.root", b));
    }

    int NPTHARDBINS = 21;
    TH1 *hNevents = new TH1D("hNevents", "Number of events", NPTHARDBINS, -0.5, double(NPTHARDBINS) - 0.5),
        *hCrossSection = new TH1D("hCrossSection", "Cross section", NPTHARDBINS, -0.5, double(NPTHARDBINS) - 0.5);
    for(auto [b, fl] : files) {
        hNevents->SetBinContent(hNevents->GetXaxis()->FindBin(b), fl.nevents);
        hCrossSection->SetBinContent(hCrossSection->GetXaxis()->FindBin(b), fl.crosssection);
    }
    auto hKt = merge(getMergeList(files, "kt", 0));
    std::vector<TH1 *> spectra, zg, rg, nsd, thetag, mergelist;
    for(auto R : ROOT::TSeqI(2,7)) {
        spectra.push_back(merge(getMergeList(files, "spectrum", R)));
        mergelist = getMergeList(files, "zg", R);
        if(mergelist.size()) zg.push_back(merge(mergelist));
        mergelist = getMergeList(files, "rg", R);
        if(mergelist.size()) rg.push_back(merge(mergelist));
        mergelist = getMergeList(files, "nsd", R);
        if(mergelist.size()) nsd.push_back(merge(mergelist));
        mergelist = getMergeList(files, "thetag", R);
        if(mergelist.size()) thetag.push_back(merge(mergelist));
    }

    std::unique_ptr<TFile> writer(TFile::Open("jetspectrum_merged.root", "RECREATE"));
    hNevents->Write();
    hCrossSection->Write();
    hKt->Write();
    writer->mkdir("Spectra");
    writer->cd("Spectra");
    for(auto s : spectra) s->Write();
    if(zg.size()) {
        writer->mkdir("Zg");
        writer->cd("Zg");
        for(auto z : zg) z->Write();
    }
    if(rg.size()) {
        writer->mkdir("Rg");
        writer->cd("Rg");
        for(auto r : rg) r->Write();
    }
    if(nsd.size()) {
        writer->mkdir("Nsd");
        writer->cd("Nsd");
        for(auto n : nsd) n->Write();
    }
    if(thetag.size()) {
        writer->mkdir("Thetag");
        writer->cd("Thetag");
        for(auto t : thetag) t->Write();
    }
}
