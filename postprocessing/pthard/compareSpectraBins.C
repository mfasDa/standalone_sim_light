std::map<int, TH1 *> readSpectra(const char *filename, int bin) {
    std::map<int, TH1 *> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    auto nevents = static_cast<TH1 *>(reader->Get("hNevents"))->GetBinContent(1);
    reader->cd("Spectra");
    for(auto R : ROOT::TSeqI(2, 7)) {
        auto spec = static_cast<TH1 *>(gDirectory->Get(Form("JetSpectrumWeightedR%02d", R)));
        spec->SetDirectory(nullptr);
        spec->SetNameTitle(Form("SpecR%02dbin%d", R, bin), Form("Spectrum for R=%.1f in bin %d", double(R)/10., bin));
        spec->Scale(1./nevents);
        result[R] = spec;
    }
    return result;
}

void compareSpectraBins() {
    auto style = [](Color_t col, Style_t mrk) {
        return [col, mrk](auto obj) {
            obj->SetMarkerColor(col);
            obj->SetLineColor(col);
            obj->SetMarkerStyle(mrk);
        };
    };

    std::vector<Color_t> colors = {kRed, kBlue, kGreen, kOrange, kMagenta, kCyan, kViolet, kGray};
    std::vector<Style_t> markers = {24, 25, 26, 27, 28};

    std::map<int, std::map<int, TH1 *>> data;
    for(auto ib : ROOT::TSeqI(0,21)) data[ib] = readSpectra(Form("bin%d/jetspectrum.root", ib), ib);

    auto plot = new ROOT6tools::TSavableCanvas("jetspectra_kthardbins", "Comparison jet spectra in kthard bins", 1200, 1000);
    plot->Divide(3,2);

    int ipad = 1;
    for(auto R : ROOT::TSeqI(2,7)) {
        plot->cd(ipad);
        gPad->SetLogy();
        gPad->SetLeftMargin(0.14);
        gPad->SetRightMargin(0.04);
        (new ROOT6tools::TAxisFrame(Form("SpecframeR%02d", R), "p_{t} (GeV/c)", "d#sigma/dp_{t} (mb/GeV/c)", 0., 500., 1e-10, 100.))->Draw("axis");
        (new ROOT6tools::TNDCLabel(0.15, 0.8, 0.4, 0.89, Form("R = %.1f", double(R)/10.)))->Draw();
        TLegend *leg = nullptr;
        if(ipad == 1) {
            leg = new ROOT6tools::TDefaultLegend(0.5, 0.5, 0.89, 0.89);
            leg->SetNColumns(2);
            leg->Draw();
        }
        TH1 *sum = nullptr;
        int icolor = 0, imarker = 0;
        for(auto ib : ROOT::TSeqI(0, 21)){
        //for(auto ib : ROOT::TSeqI(0, 5)){
            auto spec = data[ib][R];
            style(colors[icolor], markers[imarker])(spec);
            spec->Draw("epsame");
            if(leg) leg->AddEntry(spec, Form("bin %d", ib), "lep");
            if(!sum) sum = (TH1 *)spec->Clone(Form("SumR%02d", R));
            else sum->Add(spec);
            icolor++;
            imarker++;
            if(icolor == colors.size()) icolor = 0;
            if(imarker == markers.size()) imarker = 0;
        }
        style(kBlack, 30)(sum);
        sum->Draw("epsame");
        if(leg) leg->AddEntry(sum, "Sum", "lep");
        ipad++;
    }
    plot->cd();
    plot->Update();
    plot->SaveCanvas(plot->GetName());
}
