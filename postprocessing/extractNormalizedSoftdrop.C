bool hasKey(TList *keylist, const char *keyname) {
    bool found(false);
    for(auto key : TRangeDynCast<TKey>(keylist)) {
        if(std::string(key->GetName()) == keyname) {
            found = true;
            break;
        }
    }
    return found;
}

void extractNormalizedSoftdrop(const char *filename = "jetspectrum_merged.root"){
    const double kVerySmall = 1e-5;
    std::vector<double> ptbinning = {15, 20, 30, 40, 50, 60, 80, 100, 120, 140, 160, 180, 200, 240, 500};
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ")),
                           writer(TFile::Open("softdrop.root", "RECREATE"));
    auto dirs = reader->GetListOfKeys();
    std::vector<std::string> observables = {"Zg", "Rg", "Nsd", "Thetag"};
    for(auto obs : observables) {
        if(!hasKey(dirs, obs.data())) continue;
        writer->mkdir(obs.data());
        for(auto R : ROOT::TSeqI(2, 7)) {
            reader->cd(obs.data());
            auto h2D = static_cast<TH2 *>(gDirectory->Get(Form("h%sWeightR%02d", obs.data(), R)));
            h2D->SetDirectory(nullptr);
            writer->cd(obs.data());
            gDirectory->mkdir(Form("R%02d", R));
            gDirectory->cd(Form("R%02d", R));
            for(auto ib = 0; ib < ptbinning.size()-1; ib++) {
                auto ptmin = ptbinning[ib], ptmax = ptbinning[ib+1];
                auto binmin = h2D->GetYaxis()->FindBin(ptmin+kVerySmall), binmax = h2D->GetYaxis()->FindBin(ptmax-kVerySmall);
                auto projected = h2D->ProjectionX(Form("h%sR%02d_%d_%d", obs.data(), R, int(ptmin), int(ptmax)), binmin, binmax);
                projected->Scale(1./projected->Integral());
                projected->Scale(1., "width");
                projected->Write();
            }
        }
    }
}
