TH1 * readkT(const char *filename, int bin) {
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    auto nevents = static_cast<TH1 *>(reader->Get("hNevents"))->GetBinContent(1);
    auto kthist = static_cast<TH1 *>(reader->Get("hKtWeighted"));
    kthist->SetDirectory(nullptr);
    kthist->Scale(1./nevents);
    return kthist;
}

void compareKtBins() {
    auto style = [](Color_t col, Style_t mrk) {
        return [col, mrk](auto obj) {
            obj->SetMarkerColor(col);
            obj->SetLineColor(col);
            obj->SetMarkerStyle(mrk);
        };
    };

    std::vector<Color_t> colors = {kRed, kBlue, kGreen, kOrange, kMagenta, kCyan, kViolet, kGray};
    std::vector<Style_t> markers = {24, 25, 26, 27, 28};

    std::map<int, TH1 *> data;
    for(auto ib : ROOT::TSeqI(0,20)) data[ib+1] = readkT(Form("bin%d/jetspectrum.root", ib+1), ib+1);

    auto plot = new ROOT6tools::TSavableCanvas("compktbins", "Comparison kt bins", 800, 600);
    plot->SetLogy();
    (new ROOT6tools::TAxisFrame("Specframe", "p_{t} (GeV/c)", "d#sigma/dp_{t} (mb/GeV/c)", 0., 500., 1e-10, 100.))->Draw("axis");
    TLegend *leg  = new ROOT6tools::TDefaultLegend(0.5, 0.5, 0.89, 0.89);
    leg->SetNColumns(2);
    leg->Draw();
    TH1 *sum = nullptr;
    int icolor = 0, imarker = 0;
    for(auto ib : ROOT::TSeqI(0, 20)){
        auto spec = data[ib+1];
        style(colors[icolor], markers[imarker])(spec);
        spec->Draw("epsame");
        leg->AddEntry(spec, Form("bin %d", ib+1), "lep");
        if(!sum) sum = (TH1 *)spec->Clone(Form("Sum"));
        else sum->Add(spec);
        icolor++;
        imarker++;
        if(icolor == colors.size()) icolor = 0;
        if(imarker == markers.size()) imarker = 0;
    }
    style(kBlack, 30)(sum);
    sum->Draw("epsame");
    leg->AddEntry(sum, "Sum", "lep");
    plot->cd();
    plot->Update();
    plot->SaveCanvas(plot->GetName());
}
