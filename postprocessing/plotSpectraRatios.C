void plotSpectraRatios(const char *filename = "jetspectrum_merged.root") {
    std::map<int, TH1 *> spectra;
    {
        std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
        reader->cd("Spectra");

        for(auto R : ROOT::TSeqI(2,7)){
            double radius = double(R)/10.;
            auto spectrum = static_cast<TH1 *>(gDirectory->Get(Form("JetSpectrumWeightedR%02d", R)));
            spectrum->SetDirectory(nullptr);
            spectrum->Scale(1./(1.4 - 2*radius));
            spectra[R] = spectrum;
        }
    }

    auto plot = new ROOT6tools::TSavableCanvas("spectraRatios", "spectra ratios", 800, 600);
    plot->cd();
    (new ROOT6tools::TAxisFrame("ratioframe", "p_{t} (GeV/c)", "d#sigma(R=0.2)/dp_{t}/d#sigma(R=X)/dp_{t}", 0., 300, 0., 1.))->Draw("axis");
    auto leg = new ROOT6tools::TDefaultLegend(0.55, 0.15, 0.89, 0.5);
    leg->Draw();

    std::map<int, Color_t> colors = {{3, kRed}, {4, kBlue}, {5, kGreen}, {6, kViolet}};
    std::map<int, Style_t> markers = {{3, 24}, {4, 25}, {5, 26}, {6, 27}};

    auto style = [](Color_t col, Style_t mrk) {
        return [col, mrk] (auto obj) {
            obj->SetMarkerColor(col);
            obj->SetMarkerStyle(mrk);
            obj->SetLineColor(col);
        };
    };

    auto ref = spectra[2];
    for(auto R : ROOT::TSeqI(3, 7)){
        auto ratio = (TH1 *)ref->Clone(Form("SpectraRatioR02R%02d", R));
        ratio->SetDirectory(nullptr);
        ratio->Divide(ratio, spectra[R], 1., 1.);
        style(colors[R], markers[R])(ratio);
        ratio->Draw("epsame");
        leg->AddEntry(ratio, Form("R=0.2/R=%.1f", double(R) / 10.), "lep");
    }

    plot->cd();
    plot->Update();
    plot->SaveCanvas(plot->GetName());
}
