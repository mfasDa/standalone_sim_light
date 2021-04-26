struct histo {
    double ptmin;
    double ptmax;
    TH1 *histo;

    bool operator<(const struct histo &other) const { return ptmax < other.ptmin; }
};

void makePlotSoftDrop(const char *inputfile = "softdrop.root"){
    std::unique_ptr<TFile> reader(TFile::Open(inputfile, "READ"));

    auto style = [](Color_t col, Style_t mrk) {
        return [col, mrk](auto obj){
            obj->SetMarkerColor(col);
            obj->SetLineColor(col);
            obj->SetMarkerStyle(mrk);
        };
    };
    std::vector<Color_t> colors = {kRed, kBlue, kGreen, kOrange, kMagenta, kTeal, kGray, kViolet};
    std::vector<Style_t> markers = {24, 25, 26, 27, 28};


    std::vector<std::string> observables = {"Zg", "Rg", "Nsd"};

    for(auto obs : observables) {
        auto plot = new ROOT6tools::TSavableCanvas(Form("SoftDropHerwig%s", obs.data()), Form("Pt-dependence of %s", obs.data()), 1000, 800); 
        plot->Divide(3,2);
            
        int ipad = 1;
        const double ptmin = 15., ptmax = 200.;
        
        reader->cd(obs.data());
        auto basedir = gDirectory;
        auto leg = new ROOT6tools::TDefaultLegend(0.15, 0.15, 0.89, 0.89);
        for(auto R : ROOT::TSeqI(2, 7)){
            std::string rstring = Form("R%02d", R),
                        rtitle = Form("R = %.1f", double(R)/10.);
            basedir->cd(rstring.data());

            std::vector<histo> histos;
            TH1 *tmphist(nullptr);
            for(auto entry : TRangeDynCast<TKey>(gDirectory->GetListOfKeys())){
                TString histname(entry->GetName());
                std::unique_ptr<TObjArray> tokens(histname.Tokenize("_"));
                int ptmin = static_cast<TObjString*>(tokens->At(1))->String().Atoi(),
                    ptmax = static_cast<TObjString*>(tokens->At(2))->String().Atoi();
                auto dist =  entry->ReadObject<TH1>();
                dist->SetDirectory(nullptr);
                histos.push_back({static_cast<double>(ptmin), static_cast<double>(ptmax), dist});
                if(!tmphist) tmphist = dist;
            }
            std::sort(histos.begin(), histos.end(), std::less<histo>());
           

            plot->cd(ipad);
            (new ROOT6tools::TAxisFrame(Form("%sframe%s", obs.data(), rstring.data()), obs.data(), Form("1/N_{jets} dN/d%s", obs.data()), tmphist->GetXaxis()->GetBinLowEdge(1), tmphist->GetXaxis()->GetBinUpEdge(tmphist->GetXaxis()->GetNbins()), 0., 10.))->Draw("axis");
            (new ROOT6tools::TNDCLabel(0.15, 0.8, 0.25, 0.89, rtitle.data()))->Draw();

            int icol = 0, imrk = 0;
            for(auto [ptlow, pthigh, dist]: histos) {
                auto ptcent = (ptlow + pthigh) / 2.;
                if(ptcent < ptmin || ptcent > ptmax) continue;

                style(colors[icol], markers[imrk])(dist);
                dist->Draw("epsame");
                if(ipad == 1) leg->AddEntry(dist, Form("%.1f GeV/c < p_{t} < %.1f GeV/c", ptlow, pthigh), "lep");
                icol++;
                imrk++;
                if(icol == colors.size()) icol = 0;
                if(imrk == markers.size()) imrk = 0;
            }

            ipad++;
        }
        plot->cd(ipad);
        leg->Draw();
        plot->cd();
        plot->Update();
        plot->SaveCanvas(plot->GetName());
    }
}
