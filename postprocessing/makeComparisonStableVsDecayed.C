#ifndef __CLING__
#include <iostream>
#include <memory>
#include <sstream>
#include <set>
#include <string>
#include <tuple>
#include <TFile.h>
#include <TKey.h>
#include <TH1.h>
#include <RStringView.h>
#include <ROOT/TSeq.hxx>

#include <TSavableCanvas.h>
#include <TAxisFrame.h>
#include <TDefaultLegend.h>
#include <TNDCLabel.h>
#endif

struct ptbin {
	int fPtMin;
    int fPtMax;
    TH1 *fSpectrum;

    bool operator==(const ptbin &other) const { return fPtMin == other.fPtMin && fPtMax == other.fPtMax; }
    bool operator<(const ptbin &other) const { return fPtMax <= other.fPtMin;}
};

struct rbin {
    int fR;
    std::set<ptbin> fData;
    bool operator==(const rbin &other) const { return fR == other.fR; }
    bool operator<(const rbin &other) const { return fR < other.fR; }
};

std::vector<std::string> observables = {"Zg", "Rg", "Thetag", "Nsd"};

std::tuple<std::string, int, int, int> decode_histnanme(const char *histname){
    std::stringstream decoder(histname);
    std::string tmp, observable;
    int entry = 0, R, ptmin, ptmax;
    std::cout << histname << std::endl;
    while(std::getline(decoder, tmp, '_')){
        switch(entry){
            case 0: {
                auto delimiter = tmp.rfind("R");
                std::cout << tmp.substr(delimiter + 1) << std::endl;
                R = std::stoi(tmp.substr(delimiter + 1).data());
                observable = tmp.substr(1, delimiter - 1);
                break;
            }
            case 1: ptmin = std::stoi(tmp); break;
            case 2: ptmax = std::stoi(tmp); break;
        };
        entry++;
    }
    return std::make_tuple(observable, R, ptmin, ptmax);
}

std::map<std::string, std::set<rbin>> readFile(const char *filename){
    std::cout << "Start reading " << filename << std::endl;
    std::map<std::string, std::set<rbin>> result;
    std::unique_ptr<TFile> reader(TFile::Open(filename, "READ"));
    for(const auto &obs : observables) {
        reader->cd(obs.data());
        std::set<rbin> obsdists;
        auto basedir = gDirectory;
        for(auto ren : TRangeDynCast<TKey>(gDirectory->GetListOfKeys())){
            std::string_view rview(ren->GetName());
            rbin nextbin; 
            nextbin.fR = std::stoi(rview.substr(1).data());
            basedir->cd(ren->GetName());
            for(auto histkey : TRangeDynCast<TKey>(gDirectory->GetListOfKeys())){
                auto hist = histkey->ReadObject<TH1>();
                hist->SetDirectory(nullptr);
                auto [obsname, R, ptmin, ptmax] = decode_histnanme(histkey->GetName());
                nextbin.fData.insert({ptmin, ptmax, hist});
            }
            obsdists.insert(nextbin);
        }
        result[obs] = obsdists;
    }
    std::cout << "Finished reading " << filename << std::endl;
    return result;
}

void makePlots(const std::string_view observable, int R, const std::set<ptbin> &K0DecayedPi0Decayed, const std::set<ptbin> &K0DecayedPi0Stable, const std::set<ptbin> &K0StablePi0Decayed, const std::set<ptbin> &K0StablePi0Stable) {
    double textsize = 0.045;
    auto makeCanvas = [&](int index) {
        auto plot = new ROOT6tools::TSavableCanvas(Form("ComparisonPi0K0_%s_R%02d_%d", observable.data(), R, index), Form("Comparison stable/decayed, %s, R = %.1f (%d)", observable.data(), double(R)/10., index), 1200, 800);
        plot->Divide(4,2);
        return plot;
    };
    auto finishCanvas = [](ROOT6tools::TSavableCanvas *plot) {
        if(plot) {
            plot->cd();
            plot->Update();
            plot->SaveCanvas(plot->GetName());
        }
    };  

    auto makeFrame = [R, &observable, textsize](int ptmin, int ptmax, double xmin, double xmax) {
        const char *framename = Form("Frame%s_R%02d_%d_%d", observable.data(), R, ptmin, ptmax),
                   *xtitle = observable.data(),
                   *ytitle = Form("1/N_{jets} dN/d%s", observable.data()); 
        double ymin = 0,
               ymax = observable == "Nsd" ? 0.5 : 14;
        auto frame = new ROOT6tools::TAxisFrame(framename, xtitle, ytitle, xmin, xmax, ymin, ymax);
        frame->GetXaxis()->SetTitleSize(textsize);
        frame->GetXaxis()->SetLabelSize(textsize);
        frame->GetYaxis()->SetTitleSize(textsize);
        frame->GetYaxis()->SetLabelSize(textsize);
        frame->Draw("axis");
    };
    auto makeLabel = [textsize](double xmin, double ymin, double xmax, double ymax, const char *text) {
        auto label = new ROOT6tools::TNDCLabel(xmin, ymin, xmax, ymax, text);
        label->SetTextSize(textsize);
        label->Draw();
    };
    auto style = [](Color_t col, Style_t mrk) {
        return [col, mrk](auto obj){
            obj->SetMarkerColor(col);
            obj->SetLineColor(col);
            obj->SetMarkerStyle(mrk);
        };
    };
    auto draw = [style](TH1 *hist, Color_t col, Style_t mrk, TLegend *leg, const char *legentry) {
        style(col, mrk)(hist);
        hist->Draw("epsame");
        if(leg) leg->AddEntry(hist, legentry, "lep");
    };

    Color_t colK0DecayedPi0Decayed = kBlack,
            colK0StablePi0Stable = kRed,
            colK0StablePi0Decayed = kBlue,
            colK0DecayedPi0Stable = kViolet;
    Style_t mrkK0DecayedPi0Decayed = 20,
            mrkK0StablePi0Stable = 24,
            mrkK0StablePi0Decayed = 25,
            mrkK0DecayedPi0Stable = 26;

    ROOT6tools::TSavableCanvas *plot(nullptr);
    TLegend *leg(nullptr);
    int currentcanvas = 0, currentpad = 8;
    for(auto binK0DecayedPi0Decayed : K0DecayedPi0Decayed) {
        auto binK0DecayedPi0Stable = K0DecayedPi0Stable.find(binK0DecayedPi0Decayed),
             binK0StablePi0Decayed = K0StablePi0Decayed.find(binK0DecayedPi0Decayed),
             binK0StablePi0Stable = K0StablePi0Stable.find(binK0DecayedPi0Decayed);
        auto specK0DecPi0Dec = binK0DecayedPi0Decayed.fSpectrum,
             specK0DecPi0Stab = binK0DecayedPi0Stable->fSpectrum,
             specK0StabPi0Dec = binK0StablePi0Decayed->fSpectrum,
             specK0StabPi0Stab = binK0StablePi0Stable->fSpectrum;
        if(currentpad == 8) {
            finishCanvas(plot);
            plot = makeCanvas(currentcanvas);
            leg = nullptr;
            currentpad = 1;
            currentcanvas++;
        }

        plot->cd(currentpad);
        gPad->SetLeftMargin(0.15);
        gPad->SetRightMargin(0.05);
        gPad->SetTopMargin(0.05);
        makeFrame(binK0DecayedPi0Decayed.fPtMin, binK0DecayedPi0Decayed.fPtMax, specK0DecPi0Dec->GetXaxis()->GetBinLowEdge(1), specK0DecPi0Dec->GetXaxis()->GetBinUpEdge(specK0DecPi0Dec->GetXaxis()->GetNbins()));
        makeLabel(0.15, 0.85, 0.5, 0.95, Form("%d GeV/c < p_{t} < %d GeV/c", binK0DecayedPi0Decayed.fPtMin, binK0DecayedPi0Decayed.fPtMax));
        if(currentpad == 1) {
            leg = new ROOT6tools::TDefaultLegend(0.6, 0.65, 0.95, 0.95);
            leg->Draw();
            makeLabel(0.15, 0.75, 0.3, 0.85, Form("R = %.1f", double(R)/10.));
        } else {
            leg = nullptr;
        }

        draw(specK0DecPi0Dec, colK0DecayedPi0Decayed, mrkK0DecayedPi0Decayed, leg, "K_{o}^{s} dec., #pi^{0} dec.");
        draw(specK0StabPi0Stab, colK0StablePi0Stable, mrkK0StablePi0Stable, leg, "K_{o}^{s} stab., #pi^{0} stab.");
        draw(specK0DecPi0Stab, colK0DecayedPi0Stable, mrkK0DecayedPi0Stable, leg, "K_{o}^{s} dec., #pi^{0} stab.");
        draw(specK0StabPi0Dec, colK0StablePi0Decayed, mrkK0StablePi0Decayed, leg, "K_{o}^{s} stab., #pi^{0} dec.");

        currentpad++;
    }
    finishCanvas(plot);
}

void makeComparisonStableVsDecayed(){
    auto dataK0DecayedPi0Decayed = readFile("K0DecayedPi0Decayed/softdrop.root"),
         dataK0DecayedPi0Stable = readFile("K0DecayedPi0Stable/softdrop.root"),
         dataK0StablePi0Decayed = readFile("K0StablePi0Decayed/softdrop.root"),
         dataK0StablePi0Stable = readFile("K0StablePi0Stable/softdrop.root");
     
    for(const auto &obs : observables) {
        std::cout << "next observable: " << obs << std::endl;
        auto obsbinK0DecayedPi0Decayed = dataK0DecayedPi0Decayed.find(obs),
             obsbinK0DecayedPi0Stable = dataK0DecayedPi0Stable.find(obs),
             obsbinK0StablePi0Decayed = dataK0StablePi0Decayed.find(obs),
             obsbinK0StablePi0Stable = dataK0StablePi0Stable.find(obs);
        
        if(obsbinK0DecayedPi0Decayed == dataK0DecayedPi0Decayed.end()) std::cout << "Not found " << obs << " in K0 decayed Pi0 decayed" << std::endl;
        if(obsbinK0DecayedPi0Stable == dataK0DecayedPi0Stable.end()) std::cout << "Not found " << obs << " in K0 decayed Pi0 stable" << std::endl;
        if(obsbinK0StablePi0Decayed == dataK0StablePi0Decayed.end()) std::cout << "Not found " << obs << " in K0 stable Pi0 decayed" << std::endl;
        if(obsbinK0StablePi0Stable == dataK0StablePi0Stable.end()) std::cout << "Not found " << obs << " in K0 stable Pi0 stable" << std::endl;

        for(auto R : ROOT::TSeqI(2, 7)) {
            std::cout << "Doing R = " << (static_cast<double>(R)/10.) << std::endl;
            rbin search;
            search.fR = R;
            auto rbinK0DecayedPi0Decayed = obsbinK0DecayedPi0Decayed->second.find(search),
                 rbinK0DecayedPi0Stable = obsbinK0DecayedPi0Stable->second.find(search),
                 rbinK0StablePi0Decayed = obsbinK0StablePi0Decayed->second.find(search),
                 rbinK0StablePi0Stable = obsbinK0StablePi0Stable->second.find(search);
            if(rbinK0DecayedPi0Decayed == obsbinK0DecayedPi0Decayed->second.end()) std::cout << "Not found data in K0 decayed Pi0 decayed" << std::endl;
            if(rbinK0DecayedPi0Stable == obsbinK0DecayedPi0Stable->second.end()) std::cout << "Not found data in K0 decayed Pi0 stable" << std::endl;
            if(rbinK0StablePi0Decayed == obsbinK0StablePi0Decayed->second.end()) std::cout << "Not found data in K0 stable Pi0 decayed" << std::endl;
            if(rbinK0StablePi0Stable == obsbinK0StablePi0Stable->second.end()) std::cout << "Not found data in K0 stable Pi0 stable" << std::endl;
            makePlots(obs, R, rbinK0DecayedPi0Decayed->fData, rbinK0DecayedPi0Stable->fData, rbinK0StablePi0Decayed->fData, rbinK0StablePi0Stable->fData);
        }
    }
}