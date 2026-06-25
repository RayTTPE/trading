from __future__ import annotations

import math
import os
import json
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote as urlquote
from typing import Any, Callable

import numpy as np
import pandas as pd
import yfinance as yf
import requests
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# ============================================================
# LENG MARKET TERMINAL — ONE FILE EDITION
# ติดตั้งครั้งแรก:
#   pip install flask yfinance pandas numpy
# เปิดใช้งาน:
#   python Leng_Market_Terminal_OneFile.py
# แล้วเข้า http://127.0.0.1:5050
# ============================================================


PAGE_HTML = r"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Leng Market Terminal</title>
  <meta name="description" content="แดชบอร์ดดูหุ้น ETF คริปโต Forex ดัชนี และสินทรัพย์ที่ Yahoo Finance รองรับ">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Thai:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <script defer src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>

  <style>
:root{
  --bg:#070a0f;--bg-soft:#0b1018;--panel:#0f151f;--panel-2:#131b27;--line:#243041;
  --line-soft:rgba(255,255,255,.065);--text:#f2f6fb;--muted:#8290a3;--green:#00d89c;
  --green-soft:rgba(0,216,156,.12);--red:#ff5263;--red-soft:rgba(255,82,99,.12);
  --blue:#4f8cff;--yellow:#f4c766;--purple:#9b7bff;--shadow:0 22px 55px rgba(0,0,0,.30)
}
html[data-theme="light"]{
  --bg:#e9eef5;--bg-soft:#f5f8fc;--panel:#fff;--panel-2:#f7f9fc;--line:#ced7e4;
  --line-soft:rgba(15,30,50,.08);--text:#142033;--muted:#69778c;--shadow:0 18px 45px rgba(23,37,58,.10)
}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--bg);color:var(--text)}
body{font-family:"Inter","Noto Sans Thai",sans-serif;overflow-x:hidden}
button,input{font:inherit}button{color:inherit}
button:focus-visible,input:focus-visible{outline:2px solid var(--blue);outline-offset:2px}

.terminal-shell{
  min-height:100vh;display:grid;grid-template-columns:248px minmax(650px,1fr) 300px;
  grid-template-rows:66px minmax(0,1fr) 30px;
  grid-template-areas:"top top top" "watch work right" "status status status";
  background:radial-gradient(circle at 48% -20%,rgba(79,140,255,.11),transparent 35%),var(--bg)
}
.topbar{
  grid-area:top;position:sticky;top:0;z-index:100;display:grid;
  grid-template-columns:248px minmax(320px,620px) 1fr;gap:20px;align-items:center;
  padding:0 14px;border-bottom:1px solid var(--line);background:rgba(7,10,15,.94);backdrop-filter:blur(18px)
}
html[data-theme="light"] .topbar{background:rgba(245,248,252,.94)}
.brand{display:flex;align-items:center;gap:11px;color:var(--text);text-decoration:none}
.brand-mark{
  width:38px;height:38px;border-radius:10px;display:grid;place-items:center;font-weight:900;
  background:linear-gradient(145deg,var(--green),#00a8ff);color:#03110e;box-shadow:0 0 30px rgba(0,216,156,.18)
}
.brand strong,.brand small{display:block}.brand strong{font-size:13px;letter-spacing:.12em}
.brand small{font-size:10px;color:var(--muted);margin-top:3px}
.global-search{
  position:relative;height:42px;display:flex;align-items:center;gap:10px;padding:0 12px;
  border:1px solid var(--line);border-radius:10px;background:var(--panel)
}
.search-icon{font-size:20px;color:var(--muted)}.global-search input{width:100%;border:0;outline:0;background:transparent;color:var(--text)}
.global-search kbd{padding:3px 7px;border:1px solid var(--line);border-radius:5px;color:var(--muted);background:var(--bg-soft);font-size:11px}
.search-results{
  display:none;position:absolute;top:48px;left:0;right:0;max-height:420px;overflow:auto;padding:7px;
  border:1px solid var(--line);border-radius:12px;background:var(--panel-2);box-shadow:var(--shadow);z-index:150
}
.search-results.show{display:block}
.search-result{
  width:100%;display:grid;grid-template-columns:55px minmax(0,1fr) auto;gap:10px;align-items:center;
  padding:10px;border:0;border-radius:9px;background:transparent;text-align:left;cursor:pointer
}
.search-result:hover{background:var(--line-soft)}
.result-symbol{font-weight:800;color:var(--green)}.result-name{min-width:0}
.result-name strong,.result-name small{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.result-name strong{font-size:13px}.result-name small,.result-type{font-size:10px;color:var(--muted)}
.topbar-actions{justify-self:end;display:flex;align-items:center;gap:12px}
.connection-pill{display:flex;align-items:center;gap:7px;padding:7px 10px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:11px;background:var(--panel)}
.connection-pill span{width:8px;height:8px;border-radius:50%;background:var(--yellow)}
.connection-pill.online span{background:var(--green);box-shadow:0 0 12px var(--green)}
.connection-pill.offline span{background:var(--red)}
.clock{text-align:right;min-width:92px}.clock strong,.clock small{display:block}.clock strong{font-size:12px}.clock small{font-size:10px;color:var(--muted);margin-top:2px}
.icon-button,.text-button{border:1px solid var(--line);background:var(--panel);cursor:pointer}
.icon-button{width:36px;height:36px;border-radius:9px}.icon-button:hover,.text-button:hover{border-color:var(--blue)}
.text-button{padding:7px 10px;border-radius:8px;font-size:11px;color:var(--muted)}
.panel{background:linear-gradient(180deg,var(--panel),rgba(15,21,31,.94));border:1px solid var(--line);box-shadow:var(--shadow)}
html[data-theme="light"] .panel{background:var(--panel)}

.watchlist-panel{grid-area:watch;min-height:0;border-width:0 1px 0 0;box-shadow:none;padding:15px 11px}
.panel-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}
.panel-heading small{color:var(--muted);font-size:9px;font-weight:800;letter-spacing:.14em}
.panel-heading h2{margin:3px 0 0;font-size:16px}.panel-heading.compact{margin-bottom:14px}
.watchlist-tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin:15px 0 10px;padding:4px;border-radius:10px;background:var(--bg-soft)}
.watchlist-tabs button{border:0;border-radius:7px;background:transparent;padding:7px 4px;color:var(--muted);font-size:10px;cursor:pointer}
.watchlist-tabs button.active{background:var(--panel-2);color:var(--text)}
.watchlist{display:flex;flex-direction:column;gap:4px}
.watch-row{
  position:relative;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;
  width:100%;padding:10px 7px;border:1px solid transparent;border-radius:9px;background:transparent;cursor:pointer;text-align:left
}
.watch-row:hover{background:var(--line-soft)}.watch-row.active{background:var(--green-soft);border-color:rgba(0,216,156,.26)}
.watch-symbol{font-size:12px;font-weight:800}.watch-name{font-size:9px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.watch-price{text-align:right}.watch-price b,.watch-price small{display:block}.watch-price b{font-size:11px}.watch-price small{font-size:9px;margin-top:3px}
.positive{color:var(--green)!important}.negative{color:var(--red)!important}
.watch-remove{display:none;position:absolute;left:2px;top:1px;width:18px;height:18px;border:0;border-radius:50%;background:var(--red);color:#fff;font-size:11px;cursor:pointer}
.watch-row:hover .watch-remove{display:block}
.watchlist-help{display:flex;align-items:center;gap:9px;margin-top:12px;padding:11px;border:1px dashed var(--line);border-radius:10px;color:var(--muted)}
.watchlist-help span{width:27px;height:27px;border-radius:7px;display:grid;place-items:center;background:var(--line-soft);color:var(--green)}
.watchlist-help p{font-size:10px;line-height:1.45;margin:0}

.workspace{grid-area:work;min-width:0;min-height:0;padding:12px;display:flex;flex-direction:column;gap:10px}
.instrument-strip{min-height:90px;display:grid;grid-template-columns:minmax(230px,1fr) auto minmax(340px,1.2fr);align-items:center;gap:22px;padding:14px 17px;border-radius:12px}
.instrument-main{display:flex;align-items:center;gap:12px;min-width:0}
.symbol-badge{width:44px;height:44px;border-radius:11px;display:grid;place-items:center;font-weight:900;background:linear-gradient(145deg,#1d2737,#121820);border:1px solid var(--line)}
.instrument-title{display:flex;align-items:center;gap:8px}.instrument-title h1{margin:0;font-size:20px}
.instrument-title span{padding:3px 6px;border-radius:5px;background:var(--line-soft);color:var(--muted);font-size:9px}
.instrument-main p{margin:5px 0 0;color:var(--muted);font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:300px}
.favorite-btn{border:0;background:transparent;font-size:22px;color:var(--yellow);cursor:pointer;padding:0}
.live-price{text-align:right}.live-price strong{display:block;font-size:25px;letter-spacing:-.04em}.live-price span{display:block;margin-top:5px;font-size:11px;font-weight:700}
.ohlc-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.ohlc-grid div{padding:9px;border-left:1px solid var(--line)}
.ohlc-grid small,.ohlc-grid b{display:block}.ohlc-grid small{font-size:8px;color:var(--muted);letter-spacing:.09em}.ohlc-grid b{font-size:11px;margin-top:6px}

.chart-panel{position:relative;min-height:590px;flex:1;border-radius:12px;overflow:hidden}
.chart-toolbar,.indicator-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:46px;padding:7px 10px;border-bottom:1px solid var(--line)}
.timeframe-group,.chart-actions{display:flex;align-items:center;gap:3px;flex-wrap:wrap}
.timeframe-group button,.chart-actions button,.indicator-mode{border:1px solid transparent;background:transparent;border-radius:6px;padding:6px 8px;color:var(--muted);font-size:10px;cursor:pointer}
.timeframe-group button:hover,.chart-actions button:hover,.indicator-mode:hover{color:var(--text);background:var(--line-soft)}
.timeframe-group button.active,.chart-actions button.active,.indicator-mode.active{color:var(--green);border-color:rgba(0,216,156,.30);background:var(--green-soft)}
.main-chart{height:390px}.indicator-toolbar{min-height:39px;border-top:1px solid var(--line);padding:5px 10px}
.indicator-toolbar div{display:flex;gap:4px}.indicator-toolbar p{margin:0;color:var(--muted);font-size:9px}.indicator-chart{height:120px}
.chart-loader{position:absolute;inset:47px 0 0;z-index:20;display:none;place-items:center;align-content:center;gap:10px;background:rgba(7,10,15,.72);backdrop-filter:blur(3px)}
.chart-loader.show{display:grid}.chart-loader span{width:30px;height:30px;border-radius:50%;border:3px solid var(--line);border-top-color:var(--green);animation:spin .8s linear infinite}
.chart-loader p{font-size:11px;color:var(--muted)}@keyframes spin{to{transform:rotate(360deg)}}

.bottom-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:10px}
.market-card,.positions-card{min-height:185px;border-radius:12px;padding:14px}
.market-overview{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.overview-tile{padding:11px;border:1px solid var(--line);border-radius:10px;background:var(--bg-soft);cursor:pointer;text-align:left}
.overview-tile:hover{border-color:var(--blue)}.overview-tile strong,.overview-tile span,.overview-tile small{display:block}
.overview-tile strong{font-size:11px}.overview-tile span{font-size:15px;font-weight:800;margin-top:9px}.overview-tile small{font-size:9px;margin-top:5px}
.positions-list{display:flex;flex-direction:column;gap:7px;max-height:130px;overflow:auto}
.position-row{display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:center;padding:9px;border:1px solid var(--line);border-radius:9px;background:var(--bg-soft)}
.position-row strong,.position-row small{display:block}.position-row strong{font-size:11px}.position-row small{color:var(--muted);font-size:9px;margin-top:3px}
.position-side{font-size:9px;font-weight:800;padding:4px 6px;border-radius:5px}.position-side.buy{color:var(--green);background:var(--green-soft)}.position-side.sell{color:var(--red);background:var(--red-soft)}
.empty-state{color:var(--muted);font-size:11px;line-height:1.6}

.right-panel{grid-area:right;min-height:0;padding:12px 12px 12px 0;display:flex;flex-direction:column;gap:10px}
.paper-ticket,.details-card,.news-card{border-radius:12px;padding:14px}
.paper-badge{font-size:8px;font-weight:900;color:var(--yellow);padding:5px 7px;border:1px solid rgba(244,199,102,.35);border-radius:5px}
.bid-ask{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:14px}
.bid-ask button{border:1px solid var(--line);border-radius:9px;padding:11px;background:var(--bg-soft);cursor:pointer;text-align:left}
.bid-ask small,.bid-ask strong{display:block}.bid-ask small{font-size:8px;letter-spacing:.1em}.bid-ask strong{font-size:15px;margin-top:5px}
.sell-side small{color:var(--red)}.buy-side small{color:var(--green)}
.field-label{display:block;color:var(--muted);font-size:9px;margin-bottom:6px}
.stepper{display:grid;grid-template-columns:38px 1fr 38px;height:40px}
.stepper button,.stepper input{border:1px solid var(--line);background:var(--bg-soft);color:var(--text);text-align:center}
.stepper button{cursor:pointer}.stepper button:first-child{border-radius:8px 0 0 8px}.stepper button:last-child{border-radius:0 8px 8px 0}
.stepper input{min-width:0;border-left:0;border-right:0;outline:0}
.order-summary{display:flex;justify-content:space-between;gap:10px;margin:13px 0;color:var(--muted);font-size:10px}.order-summary strong{color:var(--text)}
.order-buttons{display:grid;grid-template-columns:1fr 1fr;gap:7px}.order-buttons button{height:40px;border:0;border-radius:8px;font-weight:800;cursor:pointer}
.sell-order{background:var(--red);color:#fff}.buy-order{background:var(--green);color:#03110e}
.paper-note{font-size:9px;color:var(--muted);line-height:1.5;margin:12px 0 0}
.asset-details{margin:0}.asset-details div{display:flex;justify-content:space-between;gap:10px;padding:9px 0;border-bottom:1px solid var(--line-soft)}.asset-details div:last-child{border:0}
.asset-details dt{font-size:10px;color:var(--muted)}.asset-details dd{margin:0;font-size:10px;font-weight:700;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:150px}
.news-card{flex:1;min-height:225px;overflow:hidden}.news-list{display:flex;flex-direction:column;gap:6px;max-height:260px;overflow:auto}
.news-item{display:grid;gap:4px;padding:9px;border-radius:8px;color:var(--text);text-decoration:none;border:1px solid transparent}
.news-item:hover{background:var(--line-soft);border-color:var(--line)}.news-item strong{font-size:10px;line-height:1.4}.news-item small{color:var(--muted);font-size:8px}

.statusbar{grid-area:status;display:flex;align-items:center;gap:20px;padding:0 13px;border-top:1px solid var(--line);background:var(--bg-soft);color:var(--muted);font-size:8px}
.statusbar .warning{margin-left:auto;color:var(--yellow)}
.toast{position:fixed;right:18px;bottom:42px;z-index:500;width:min(340px,calc(100% - 30px));padding:13px 15px;border:1px solid var(--line);border-radius:11px;background:var(--panel-2);box-shadow:var(--shadow);opacity:0;pointer-events:none;transform:translateY(14px);transition:.25s}
.toast.show{opacity:1;transform:none}.toast strong{font-size:12px}.toast p{font-size:10px;color:var(--muted);line-height:1.5;margin:5px 0 0}

@media(max-width:1280px){
  .terminal-shell{grid-template-columns:220px minmax(580px,1fr);grid-template-areas:"top top" "watch work" "status status"}
  .topbar{grid-template-columns:220px minmax(300px,1fr) auto}.right-panel{display:none}
  .instrument-strip{grid-template-columns:minmax(200px,1fr) auto}.ohlc-grid{grid-column:1/-1}
}
@media(max-width:900px){
  .terminal-shell{display:block;min-width:0}.topbar{position:sticky;grid-template-columns:1fr auto;height:auto;min-height:64px;padding:10px}
  .brand small,.connection-pill,.clock{display:none}.global-search{grid-column:1/-1;grid-row:2}
  .watchlist-panel{position:relative;display:block;padding:10px;border-right:0;border-bottom:1px solid var(--line)}
  .watchlist{display:flex;flex-direction:row;overflow-x:auto;padding-bottom:4px}.watch-row{flex:0 0 150px}.watchlist-help,.watchlist-tabs{display:none}
  .workspace{padding:8px}.instrument-strip{grid-template-columns:1fr auto;gap:12px}.ohlc-grid{grid-column:1/-1}
  .chart-toolbar{align-items:flex-start;flex-direction:column}.main-chart{height:360px}.bottom-grid{grid-template-columns:1fr}.market-overview{grid-template-columns:repeat(2,1fr)}
  .right-panel{display:none}.statusbar{display:none}
}
@media(max-width:560px){
  .instrument-strip{grid-template-columns:1fr}.live-price{text-align:left}.ohlc-grid{grid-template-columns:repeat(2,1fr)}
  .main-chart{height:315px}.indicator-toolbar p{display:none}.chart-panel{min-height:535px}
}

  </style>
  <script defer>
"use strict";

const clone = value => JSON.parse(JSON.stringify(value));

const DEFAULT_WATCHLIST = [
  {symbol:"AAPL",name:"Apple"},
  {symbol:"NVDA",name:"NVIDIA"},
  {symbol:"TSLA",name:"Tesla"},
  {symbol:"MSFT",name:"Microsoft"},
  {symbol:"PTT.BK",name:"PTT"},
  {symbol:"DELTA.BK",name:"Delta Thailand"},
  {symbol:"BTC-USD",name:"Bitcoin"},
  {symbol:"GC=F",name:"Gold Futures"}
];

const THAI_LIST = [
  {symbol:"PTT.BK",name:"PTT"},{symbol:"DELTA.BK",name:"Delta Thailand"},
  {symbol:"CPALL.BK",name:"CP All"},{symbol:"AOT.BK",name:"Airports of Thailand"},
  {symbol:"ADVANC.BK",name:"Advanced Info Service"},{symbol:"KBANK.BK",name:"Kasikornbank"}
];

const GLOBAL_LIST = [
  {symbol:"AAPL",name:"Apple"},{symbol:"NVDA",name:"NVIDIA"},{symbol:"TSLA",name:"Tesla"},
  {symbol:"MSFT",name:"Microsoft"},{symbol:"AMZN",name:"Amazon"},{symbol:"META",name:"Meta"}
];

const OVERVIEW_SYMBOLS = [
  {symbol:"^GSPC",name:"S&P 500"},
  {symbol:"^IXIC",name:"NASDAQ"},
  {symbol:"^SET.BK",name:"SET Index"},
  {symbol:"BTC-USD",name:"Bitcoin"}
];

const $ = id => document.getElementById(id);

function loadJSON(key,fallback){
  try{
    const raw=localStorage.getItem(key);
    return raw?JSON.parse(raw):clone(fallback);
  }catch{
    return clone(fallback);
  }
}
function saveJSON(key,value){localStorage.setItem(key,JSON.stringify(value));}

const state={
  symbol:"AAPL",name:"Apple Inc.",period:"3mo",interval:"1d",
  chartMode:"candles",indicatorMode:"rsi",quote:null,history:null,
  watchlist:loadJSON("leng_watchlist",DEFAULT_WATCHLIST),
  positions:loadJSON("leng_paper_positions",[]),
  visibleList:"favorites",
  theme:localStorage.getItem("leng_terminal_theme")||"dark",
  searchTimer:null
};

let mainChart,indicatorChart,candleSeries,priceLineSeries,volumeSeries;
let sma20Series,sma50Series,ema20Series,rsiSeries,macdSeries,macdSignalSeries,macdHistogramSeries;

function cssVar(name){return getComputedStyle(document.documentElement).getPropertyValue(name).trim();}

function chartOptions(){
  return{
    layout:{background:{type:"solid",color:cssVar("--panel")},textColor:cssVar("--muted"),fontFamily:"Inter, Noto Sans Thai, sans-serif",fontSize:10,attributionLogo:false},
    grid:{vertLines:{color:cssVar("--line-soft")},horzLines:{color:cssVar("--line-soft")}},
    crosshair:{
      vertLine:{color:"#65748a",width:1,style:2,labelBackgroundColor:"#263344"},
      horzLine:{color:"#65748a",width:1,style:2,labelBackgroundColor:"#263344"}
    },
    rightPriceScale:{borderColor:cssVar("--line"),scaleMargins:{top:.08,bottom:.23}},
    timeScale:{borderColor:cssVar("--line"),timeVisible:true,secondsVisible:false},
    handleScroll:{mouseWheel:true,pressedMouseMove:true,horzTouchDrag:true,vertTouchDrag:false},
    handleScale:{axisPressedMouseMove:true,mouseWheel:true,pinch:true}
  };
}

function createSeriesCompat(chart,typeName,legacyMethod,options){
  if(chart.addSeries && window.LightweightCharts[typeName]){
    return chart.addSeries(window.LightweightCharts[typeName],options);
  }
  return chart[legacyMethod](options);
}

function initCharts(){
  if(!window.LightweightCharts){
    toast("โหลดกราฟไม่สำเร็จ","ไม่พบ Lightweight Charts");
    return;
  }

  mainChart=LightweightCharts.createChart($("mainChart"),chartOptions());
  indicatorChart=LightweightCharts.createChart($("indicatorChart"),{
    ...chartOptions(),
    rightPriceScale:{borderColor:cssVar("--line"),scaleMargins:{top:.12,bottom:.12}},
    timeScale:{visible:false,borderColor:cssVar("--line"),timeVisible:true}
  });

  candleSeries=createSeriesCompat(mainChart,"CandlestickSeries","addCandlestickSeries",{
    upColor:"#00d89c",downColor:"#ff5263",borderUpColor:"#00d89c",borderDownColor:"#ff5263",
    wickUpColor:"#00d89c",wickDownColor:"#ff5263",priceLineVisible:true
  });
  priceLineSeries=createSeriesCompat(mainChart,"LineSeries","addLineSeries",{
    color:"#4f8cff",lineWidth:2,visible:false,priceLineVisible:true
  });
  volumeSeries=createSeriesCompat(mainChart,"HistogramSeries","addHistogramSeries",{
    priceFormat:{type:"volume"},priceScaleId:"",priceLineVisible:false,lastValueVisible:false
  });
  volumeSeries.priceScale().applyOptions({scaleMargins:{top:.80,bottom:0}});

  sma20Series=createSeriesCompat(mainChart,"LineSeries","addLineSeries",{
    color:"#f4c766",lineWidth:1,priceLineVisible:false,lastValueVisible:false
  });
  sma50Series=createSeriesCompat(mainChart,"LineSeries","addLineSeries",{
    color:"#9b7bff",lineWidth:1,priceLineVisible:false,lastValueVisible:false,visible:false
  });
  ema20Series=createSeriesCompat(mainChart,"LineSeries","addLineSeries",{
    color:"#4f8cff",lineWidth:1,priceLineVisible:false,lastValueVisible:false,visible:false
  });

  rsiSeries=createSeriesCompat(indicatorChart,"LineSeries","addLineSeries",{
    color:"#9b7bff",lineWidth:2,priceLineVisible:false
  });
  rsiSeries.createPriceLine({price:70,color:"rgba(255,82,99,.55)",lineWidth:1,lineStyle:2,axisLabelVisible:true,title:"70"});
  rsiSeries.createPriceLine({price:30,color:"rgba(0,216,156,.55)",lineWidth:1,lineStyle:2,axisLabelVisible:true,title:"30"});

  macdSeries=createSeriesCompat(indicatorChart,"LineSeries","addLineSeries",{
    color:"#4f8cff",lineWidth:2,priceLineVisible:false,visible:false
  });
  macdSignalSeries=createSeriesCompat(indicatorChart,"LineSeries","addLineSeries",{
    color:"#f4c766",lineWidth:1,priceLineVisible:false,visible:false
  });
  macdHistogramSeries=createSeriesCompat(indicatorChart,"HistogramSeries","addHistogramSeries",{
    priceLineVisible:false,lastValueVisible:false,visible:false
  });

  mainChart.timeScale().subscribeVisibleLogicalRangeChange(range=>{
    if(range) indicatorChart.timeScale().setVisibleLogicalRange(range);
  });

  mainChart.subscribeCrosshairMove(param=>{
    if(!param||!param.time){
      $("crosshairText").textContent="เลื่อนเมาส์บนกราฟเพื่อดูราคาแต่ละแท่ง";
      return;
    }
    const data=param.seriesData.get(candleSeries)||param.seriesData.get(priceLineSeries);
    if(!data)return;
    if(data.open!==undefined){
      $("crosshairText").textContent=`O ${formatPrice(data.open)}  H ${formatPrice(data.high)}  L ${formatPrice(data.low)}  C ${formatPrice(data.close)}`;
    }else{
      $("crosshairText").textContent=`Price ${formatPrice(data.value)}`;
    }
  });

  const resize=()=>{
    if(mainChart)$("mainChart").clientWidth&&mainChart.applyOptions({width:$("mainChart").clientWidth,height:$("mainChart").clientHeight});
    if(indicatorChart)$("indicatorChart").clientWidth&&indicatorChart.applyOptions({width:$("indicatorChart").clientWidth,height:$("indicatorChart").clientHeight});
  };
  new ResizeObserver(resize).observe($("mainChart"));
  new ResizeObserver(resize).observe($("indicatorChart"));
  resize();
}

function applyChartTheme(){
  if(!mainChart||!indicatorChart)return;
  mainChart.applyOptions(chartOptions());
  indicatorChart.applyOptions({
    ...chartOptions(),
    rightPriceScale:{borderColor:cssVar("--line"),scaleMargins:{top:.12,bottom:.12}},
    timeScale:{visible:false,borderColor:cssVar("--line"),timeVisible:true}
  });
}

async function api(url){
  const response=await fetch(url,{headers:{Accept:"application/json"}});
  const data=await response.json().catch(()=>({ok:false,error:"Invalid server response"}));
  if(!response.ok||data.ok===false)throw new Error(data.error||"Request failed");
  return data;
}

function toast(title,message){
  $("toastTitle").textContent=title;
  $("toastMessage").textContent=message;
  $("toast").classList.add("show");
  clearTimeout(toast.timer);
  toast.timer=setTimeout(()=>$("toast").classList.remove("show"),3200);
}
function showLoader(show){$("chartLoader").classList.toggle("show",show);}

function formatPrice(value){
  const n=Number(value);
  if(!Number.isFinite(n))return"--";
  const digits=Math.abs(n)>=1000?2:Math.abs(n)>=1?2:6;
  return new Intl.NumberFormat("en-US",{maximumFractionDigits:digits,minimumFractionDigits:digits}).format(n);
}
function formatCompact(value){
  const n=Number(value);
  if(!Number.isFinite(n))return"--";
  return new Intl.NumberFormat("en-US",{notation:"compact",maximumFractionDigits:2}).format(n);
}
function priceWithCurrency(value){
  const currency=state.quote?.currency||"";
  return`${formatPrice(value)}${currency?" "+currency:""}`;
}
function colorize(el,value){
  el.classList.remove("positive","negative");
  el.classList.add(Number(value)>=0?"positive":"negative");
}
function escapeHTML(value){
  return String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[ch]));
}

async function healthCheck(){
  try{
    await api("/api/health");
    $("connectionText").textContent="Live";
    document.querySelector(".connection-pill").classList.add("online");
    document.querySelector(".connection-pill").classList.remove("offline");
  }catch{
    $("connectionText").textContent="Offline";
    document.querySelector(".connection-pill").classList.add("offline");
    document.querySelector(".connection-pill").classList.remove("online");
  }
}

async function loadInstrument(symbol,name){
  const cleaned=String(symbol||"").trim().toUpperCase();
  if(!cleaned)return;
  state.symbol=cleaned;
  if(name)state.name=name;
  $("symbolSearch").value="";
  closeSearchResults();
  renderWatchlist();
  showLoader(true);

  try{
    const[history,quote]=await Promise.all([
      api(`/api/history?symbol=${encodeURIComponent(cleaned)}&period=${state.period}&interval=${state.interval}`),
      api(`/api/quote?symbol=${encodeURIComponent(cleaned)}`)
    ]);
    state.history=history;
    state.quote=quote;
    state.name=quote.name||name||cleaned;
    renderHeader();
    updateCharts();
    renderOrderTicket();
    $("lastUpdated").textContent="Last update: "+new Date().toLocaleTimeString("th-TH");
    setTimeout(()=>loadNews(cleaned),700);
    setTimeout(loadWatchlistQuotes,1400);
  }catch(error){
    toast("โหลดสินทรัพย์ไม่สำเร็จ",error.message);
  }finally{
    showLoader(false);
  }
}

function renderHeader(){
  const q=state.quote||{},h=state.history?.summary||{};
  $("instrumentSymbol").textContent=state.symbol;
  $("instrumentName").textContent=state.name||state.symbol;
  $("instrumentExchange").textContent=q.exchange||q.quoteType||"MARKET";
  $("symbolBadge").textContent=state.symbol.replace(/[^A-Z0-9]/g,"")[0]||"M";
  $("livePrice").textContent=priceWithCurrency(q.price);
  $("liveChange").textContent=`${q.change>=0?"+":""}${formatPrice(q.change)} (${q.changePercent>=0?"+":""}${Number(q.changePercent||0).toFixed(2)}%)`;
  colorize($("liveChange"),q.change);
  $("statOpen").textContent=formatPrice(q.open??h.open);
  $("statHigh").textContent=formatPrice(q.high??h.high);
  $("statLow").textContent=formatPrice(q.low??h.low);
  $("statVolume").textContent=formatCompact(q.volume??h.volume);
  $("detailType").textContent=q.quoteType||"Market Asset";
  $("detailExchange").textContent=q.exchange||"--";
  $("detailCurrency").textContent=q.currency||"--";
  $("detailMarketCap").textContent=formatCompact(q.marketCap);
  $("detailBars").textContent=h.bars??"--";
  $("favoriteBtn").textContent=state.watchlist.some(item=>item.symbol===state.symbol)?"★":"☆";
}

function updateCharts(){
  if(!state.history||!mainChart)return;
  const{candles,volume,indicators}=state.history;
  candleSeries.setData(candles);
  priceLineSeries.setData(candles.map(item=>({time:item.time,value:item.close})));
  volumeSeries.setData(volume.map(item=>({
    time:item.time,value:item.value,
    color:item.direction==="up"?"rgba(0,216,156,.34)":"rgba(255,82,99,.34)"
  })));
  sma20Series.setData(indicators.sma20||[]);
  sma50Series.setData(indicators.sma50||[]);
  ema20Series.setData(indicators.ema20||[]);
  rsiSeries.setData(indicators.rsi14||[]);
  macdSeries.setData(indicators.macd||[]);
  macdSignalSeries.setData(indicators.macdSignal||[]);
  macdHistogramSeries.setData((indicators.macdHist||[]).map(item=>({
    time:item.time,value:item.value,
    color:item.direction==="up"?"rgba(0,216,156,.50)":"rgba(255,82,99,.50)"
  })));
  mainChart.timeScale().fitContent();
  indicatorChart.timeScale().fitContent();
  applyChartMode();
  applyIndicatorMode();
}

function applyChartMode(){
  const candlesVisible=state.chartMode==="candles";
  candleSeries.applyOptions({visible:candlesVisible});
  priceLineSeries.applyOptions({visible:!candlesVisible});
  $("candleBtn").classList.toggle("active",candlesVisible);
  $("lineBtn").classList.toggle("active",!candlesVisible);
}
function applyIndicatorMode(){
  const isRsi=state.indicatorMode==="rsi";
  rsiSeries.applyOptions({visible:isRsi});
  macdSeries.applyOptions({visible:!isRsi});
  macdSignalSeries.applyOptions({visible:!isRsi});
  macdHistogramSeries.applyOptions({visible:!isRsi});
  document.querySelectorAll(".indicator-mode").forEach(btn=>btn.classList.toggle("active",btn.dataset.mode===state.indicatorMode));
  indicatorChart.timeScale().fitContent();
}

function currentList(){
  if(state.visibleList==="thai")return THAI_LIST;
  if(state.visibleList==="global")return GLOBAL_LIST;
  return state.watchlist;
}

function renderWatchlist(){
  const list=$("watchlist");
  list.innerHTML="";
  currentList().forEach(item=>{
    const row=document.createElement("button");
    row.className="watch-row"+(item.symbol===state.symbol?" active":"");
    row.innerHTML=`
      <div><div class="watch-symbol">${escapeHTML(item.symbol)}</div><div class="watch-name">${escapeHTML(item.name||item.symbol)}</div></div>
      <div class="watch-price"><b data-watch-price="${escapeHTML(item.symbol)}">--</b><small data-watch-change="${escapeHTML(item.symbol)}">--</small></div>`;
    row.addEventListener("click",()=>loadInstrument(item.symbol,item.name));

    if(state.visibleList==="favorites"&&state.watchlist.length>1){
      const remove=document.createElement("button");
      remove.type="button";remove.className="watch-remove";remove.textContent="×";
      remove.addEventListener("click",event=>{
        event.stopPropagation();
        state.watchlist=state.watchlist.filter(w=>w.symbol!==item.symbol);
        saveJSON("leng_watchlist",state.watchlist);
        renderWatchlist();loadWatchlistQuotes();
      });
      row.appendChild(remove);
    }
    list.appendChild(row);
  });
}

async function loadWatchlistQuotes(){
  const items=currentList().slice(0,10);
  await Promise.allSettled(items.map(async item=>{
    try{
      const quote=item.symbol===state.symbol&&state.quote?state.quote:await api(`/api/quote?symbol=${encodeURIComponent(item.symbol)}`);
      const priceEl=document.querySelector(`[data-watch-price="${CSS.escape(item.symbol)}"]`);
      const changeEl=document.querySelector(`[data-watch-change="${CSS.escape(item.symbol)}"]`);
      if(priceEl)priceEl.textContent=formatPrice(quote.price);
      if(changeEl){
        changeEl.textContent=`${quote.changePercent>=0?"+":""}${Number(quote.changePercent).toFixed(2)}%`;
        colorize(changeEl,quote.changePercent);
      }
    }catch{}
  }));
}

async function loadMarketOverview(){
  const container=$("marketOverview");
  container.innerHTML=OVERVIEW_SYMBOLS.map(item=>`
    <button class="overview-tile" data-overview="${escapeHTML(item.symbol)}">
      <strong>${escapeHTML(item.name)}</strong><span>--</span><small>Loading...</small>
    </button>`).join("");

  document.querySelectorAll("[data-overview]").forEach((tile,index)=>{
    tile.addEventListener("click",()=>loadInstrument(OVERVIEW_SYMBOLS[index].symbol,OVERVIEW_SYMBOLS[index].name));
  });

  await Promise.allSettled(OVERVIEW_SYMBOLS.map(async item=>{
    try{
      const quote=await api(`/api/quote?symbol=${encodeURIComponent(item.symbol)}`);
      const tile=document.querySelector(`[data-overview="${CSS.escape(item.symbol)}"]`);
      if(!tile)return;
      tile.querySelector("span").textContent=formatPrice(quote.price);
      const small=tile.querySelector("small");
      small.textContent=`${quote.changePercent>=0?"+":""}${Number(quote.changePercent).toFixed(2)}%`;
      colorize(small,quote.changePercent);
    }catch{}
  }));
}

function toggleFavorite(){
  const index=state.watchlist.findIndex(item=>item.symbol===state.symbol);
  if(index>=0){
    state.watchlist.splice(index,1);
    toast("นำออกจาก Watchlist",state.symbol);
  }else{
    state.watchlist.unshift({symbol:state.symbol,name:state.name||state.symbol});
    toast("เพิ่มเข้า Watchlist แล้ว",state.symbol);
  }
  if(!state.watchlist.length)state.watchlist=clone(DEFAULT_WATCHLIST);
  saveJSON("leng_watchlist",state.watchlist);
  renderHeader();renderWatchlist();loadWatchlistQuotes();
}

function renderOrderTicket(){
  const price=Number(state.quote?.price||0);
  const spread=Math.max(price*.0003,.000001);
  $("sellPrice").textContent=formatPrice(price-spread);
  $("buyPrice").textContent=formatPrice(price+spread);
  updateEstimatedValue();
}
function updateEstimatedValue(){
  const qty=Math.max(0,Number($("orderQty").value||0));
  $("estimatedValue").textContent=priceWithCurrency(qty*Number(state.quote?.price||0));
}
function createPaperPosition(side){
  if(!state.quote)return;
  const qty=Math.max(.0001,Number($("orderQty").value||0));
  const position={
    id:Date.now(),symbol:state.symbol,name:state.name,side,qty,
    price:Number(state.quote.price),currency:state.quote.currency||"",time:new Date().toISOString()
  };
  state.positions.unshift(position);
  state.positions=state.positions.slice(0,20);
  saveJSON("leng_paper_positions",state.positions);
  renderPositions();
  toast("Paper order recorded",`${side.toUpperCase()} ${qty} ${state.symbol} @ ${formatPrice(position.price)}`);
}
function renderPositions(){
  const container=$("paperPositions");
  if(!state.positions.length){
    container.innerHTML=`<p class="empty-state">ยังไม่มีรายการจำลอง กด BUY หรือ SELL ใน Paper Order เพื่อทดสอบหน้าจอ</p>`;
    return;
  }
  container.innerHTML=state.positions.map(p=>`
    <div class="position-row">
      <div><strong>${escapeHTML(p.symbol)}</strong><small>${escapeHTML(p.qty)} @ ${formatPrice(p.price)} ${escapeHTML(p.currency||"")}</small></div>
      <span class="position-side ${p.side}">${p.side.toUpperCase()}</span>
      <small>${new Date(p.time).toLocaleTimeString("th-TH",{hour:"2-digit",minute:"2-digit"})}</small>
    </div>`).join("");
}

async function loadNews(symbol){
  const container=$("newsList");
  container.innerHTML=`<p class="empty-state">กำลังโหลดข่าวของ ${escapeHTML(symbol)}...</p>`;
  try{
    const data=await api(`/api/news?symbol=${encodeURIComponent(symbol)}`);
    if(!data.results?.length){
      container.innerHTML=`<p class="empty-state">ยังไม่พบข่าวจากแหล่งข้อมูลสำหรับสินทรัพย์นี้</p>`;
      return;
    }
    container.innerHTML=data.results.map(item=>`
      <a class="news-item" href="${escapeHTML(item.url||"#")}" target="_blank" rel="noopener noreferrer">
        <strong>${escapeHTML(item.title||"Market news")}</strong>
        <small>${escapeHTML([item.publisher,item.published].filter(Boolean).join(" • "))}</small>
      </a>`).join("");
  }catch{
    container.innerHTML=`<p class="empty-state">ไม่สามารถโหลดข่าวได้ในขณะนี้</p>`;
  }
}

async function searchSymbols(query){
  const container=$("searchResults");
  if(!query.trim()){closeSearchResults();return;}
  try{
    const data=await api(`/api/search?q=${encodeURIComponent(query.trim())}`);
    if(!data.results.length){
      container.innerHTML=`<div class="empty-state" style="padding:12px">ไม่พบผลลัพธ์</div>`;
      container.classList.add("show");
      return;
    }
    container.innerHTML="";
    data.results.forEach(item=>{
      const btn=document.createElement("button");
      btn.className="search-result";
      btn.innerHTML=`
        <span class="result-symbol">${escapeHTML(item.symbol)}</span>
        <span class="result-name"><strong>${escapeHTML(item.name)}</strong><small>${escapeHTML(item.exchange||"")}</small></span>
        <span class="result-type">${escapeHTML(item.type||"")}</span>`;
      btn.addEventListener("click",()=>loadInstrument(item.symbol,item.name));
      container.appendChild(btn);
    });
    container.classList.add("show");
  }catch(error){
    container.innerHTML=`<div class="empty-state" style="padding:12px">${escapeHTML(error.message)}</div>`;
    container.classList.add("show");
  }
}
function closeSearchResults(){$("searchResults").classList.remove("show");}

function setVisibleList(type){
  state.visibleList=type;
  document.querySelectorAll(".watchlist-tabs button").forEach(btn=>btn.classList.toggle("active",btn.dataset.list===type));
  renderWatchlist();loadWatchlistQuotes();
}
function updateClock(){
  const now=new Date();
  $("clockTime").textContent=now.toLocaleTimeString("en-GB");
  $("clockDate").textContent=now.toLocaleDateString("th-TH",{day:"2-digit",month:"short",year:"numeric"});
}
function applyTheme(){
  document.documentElement.dataset.theme=state.theme;
  localStorage.setItem("leng_terminal_theme",state.theme);
  setTimeout(applyChartTheme,0);
}

function bindEvents(){
  $("symbolSearch").addEventListener("input",event=>{
    clearTimeout(state.searchTimer);
    state.searchTimer=setTimeout(()=>searchSymbols(event.target.value),280);
  });
  $("symbolSearch").addEventListener("keydown",event=>{
    if(event.key==="Escape")closeSearchResults();
    if(event.key==="Enter"){
      const first=$("searchResults").querySelector(".search-result");
      if(first)first.click();
      else if(event.target.value.trim())loadInstrument(event.target.value.trim());
    }
  });
  document.addEventListener("keydown",event=>{
    if(event.key==="/"&&document.activeElement!==$("symbolSearch")){
      event.preventDefault();$("symbolSearch").focus();
    }
  });
  document.addEventListener("click",event=>{
    if(!event.target.closest(".global-search"))closeSearchResults();
  });

  $("timeframes").addEventListener("click",event=>{
    const btn=event.target.closest("button[data-period]");
    if(!btn)return;
    state.period=btn.dataset.period;state.interval=btn.dataset.interval;
    document.querySelectorAll("#timeframes button").forEach(b=>b.classList.toggle("active",b===btn));
    loadInstrument(state.symbol,state.name);
  });

  $("candleBtn").addEventListener("click",()=>{state.chartMode="candles";applyChartMode();});
  $("lineBtn").addEventListener("click",()=>{state.chartMode="line";applyChartMode();});
  document.querySelectorAll(".indicator-toggle").forEach(btn=>{
    btn.addEventListener("click",()=>{
      btn.classList.toggle("active");
      const series={sma20:sma20Series,sma50:sma50Series,ema20:ema20Series}[btn.dataset.indicator];
      series?.applyOptions({visible:btn.classList.contains("active")});
    });
  });
  document.querySelectorAll(".indicator-mode").forEach(btn=>{
    btn.addEventListener("click",()=>{state.indicatorMode=btn.dataset.mode;applyIndicatorMode();});
  });
  $("fitChartBtn").addEventListener("click",()=>{mainChart.timeScale().fitContent();indicatorChart.timeScale().fitContent();});
  $("favoriteBtn").addEventListener("click",toggleFavorite);
  $("refreshWatchlist").addEventListener("click",()=>{loadWatchlistQuotes();loadMarketOverview();toast("Refreshing","กำลังอัปเดตราคาในรายการ");});
  document.querySelectorAll(".watchlist-tabs button").forEach(btn=>btn.addEventListener("click",()=>setVisibleList(btn.dataset.list)));
  $("themeBtn").addEventListener("click",()=>{state.theme=state.theme==="dark"?"light":"dark";applyTheme();});

  $("orderQty").addEventListener("input",updateEstimatedValue);
  $("qtyMinus").addEventListener("click",()=>{
    $("orderQty").value=Math.max(.0001,Number($("orderQty").value||1)-1);updateEstimatedValue();
  });
  $("qtyPlus").addEventListener("click",()=>{
    $("orderQty").value=Number($("orderQty").value||0)+1;updateEstimatedValue();
  });
  $("paperBuyBtn").addEventListener("click",()=>createPaperPosition("buy"));
  $("paperSellBtn").addEventListener("click",()=>createPaperPosition("sell"));
  $("buyPreset").addEventListener("click",()=>createPaperPosition("buy"));
  $("sellPreset").addEventListener("click",()=>createPaperPosition("sell"));
  $("clearPositions").addEventListener("click",()=>{
    state.positions=[];saveJSON("leng_paper_positions",state.positions);renderPositions();
  });
}

async function boot(){
  applyTheme();
  updateClock();
  setInterval(updateClock,1000);
  bindEvents();
  initCharts();
  renderWatchlist();
  renderPositions();
  await healthCheck();
  await loadInstrument(state.symbol,state.name);
  setTimeout(loadMarketOverview,1200);
  setInterval(()=>{
    if(document.visibilityState==="visible"){
      loadInstrument(state.symbol,state.name);
      loadMarketOverview();
    }
  },90000);
}
window.addEventListener("DOMContentLoaded",boot);

  </script>

</head>
<body>
<div class="terminal-shell">
  <header class="topbar">
    <a class="brand" href="#">
      <span class="brand-mark">L</span>
      <span><strong>LENG TERMINAL</strong><small>Market Intelligence Dashboard</small></span>
    </a>
    <div class="global-search">
      <span class="search-icon">⌕</span>
      <input id="symbolSearch" autocomplete="off" placeholder="ค้นหา AAPL, PTT.BK, BTC-USD, XAU/USD, EURUSD=X...">
      <kbd>/</kbd>
      <div id="searchResults" class="search-results"></div>
    </div>
    <div class="topbar-actions">
      <div class="connection-pill"><span></span><b id="connectionText">Connecting</b></div>
      <div class="clock"><strong id="clockTime">--:--:--</strong><small id="clockDate">Bangkok</small></div>
      <button id="themeBtn" class="icon-button" title="เปลี่ยนธีม">◐</button>
    </div>
  </header>

  <aside class="watchlist-panel panel">
    <div class="panel-heading">
      <div><small>WORKSPACE</small><h2>Watchlist</h2></div>
      <button id="refreshWatchlist" class="icon-button" title="รีเฟรช">↻</button>
    </div>
    <div class="watchlist-tabs">
      <button class="active" data-list="favorites">Favorites</button>
      <button data-list="thai">Thai</button>
      <button data-list="global">Global</button>
    </div>
    <div id="watchlist" class="watchlist"></div>
    <div class="watchlist-help"><span>+</span><p>ค้นหาสัญลักษณ์ด้านบน แล้วกดดาวเพื่อเพิ่มรายการโปรด</p></div>
  </aside>

  <main class="workspace">
    <section class="instrument-strip panel">
      <div class="instrument-main">
        <div class="symbol-badge" id="symbolBadge">A</div>
        <div>
          <div class="instrument-title">
            <h1 id="instrumentSymbol">AAPL</h1>
            <span id="instrumentExchange">NASDAQ</span>
            <button id="favoriteBtn" class="favorite-btn" title="เพิ่ม Watchlist">☆</button>
          </div>
          <p id="instrumentName">Apple Inc.</p>
        </div>
      </div>
      <div class="live-price"><strong id="livePrice">--</strong><span id="liveChange">--</span></div>
      <div class="ohlc-grid">
        <div><small>OPEN</small><b id="statOpen">--</b></div>
        <div><small>HIGH</small><b id="statHigh">--</b></div>
        <div><small>LOW</small><b id="statLow">--</b></div>
        <div><small>VOLUME</small><b id="statVolume">--</b></div>
      </div>
    </section>

    <section class="chart-panel panel">
      <div class="chart-toolbar">
        <div class="timeframe-group" id="timeframes">
          <button data-period="1d" data-interval="1m">1D</button>
          <button data-period="5d" data-interval="5m">5D</button>
          <button data-period="1mo" data-interval="30m">1M</button>
          <button class="active" data-period="3mo" data-interval="1d">3M</button>
          <button data-period="6mo" data-interval="1d">6M</button>
          <button data-period="1y" data-interval="1d">1Y</button>
          <button data-period="5y" data-interval="1wk">5Y</button>
          <button data-period="max" data-interval="1mo">MAX</button>
        </div>
        <div class="chart-actions">
          <button id="candleBtn" class="active">Candles</button>
          <button id="lineBtn">Line</button>
          <button data-indicator="sma20" class="indicator-toggle active">MA20</button>
          <button data-indicator="sma50" class="indicator-toggle">MA50</button>
          <button data-indicator="ema20" class="indicator-toggle">EMA20</button>
          <button id="fitChartBtn" title="จัดกราฟให้พอดี">⌗</button>
        </div>
      </div>
      <div id="chartLoader" class="chart-loader"><span></span><p>กำลังโหลดข้อมูลตลาด...</p></div>
      <div id="mainChart" class="main-chart"></div>
      <div class="indicator-toolbar">
        <div>
          <button class="indicator-mode active" data-mode="rsi">RSI 14</button>
          <button class="indicator-mode" data-mode="macd">MACD</button>
        </div>
        <p id="crosshairText">เลื่อนเมาส์บนกราฟเพื่อดูราคาแต่ละแท่ง</p>
      </div>
      <div id="indicatorChart" class="indicator-chart"></div>
    </section>

    <section class="bottom-grid">
      <article class="market-card panel">
        <div class="panel-heading compact"><div><small>SNAPSHOT</small><h2>Market Overview</h2></div></div>
        <div id="marketOverview" class="market-overview"></div>
      </article>
      <article class="positions-card panel">
        <div class="panel-heading compact">
          <div><small>LOCAL SIMULATION</small><h2>Paper Positions</h2></div>
          <button id="clearPositions" class="text-button">Clear</button>
        </div>
        <div id="paperPositions" class="positions-list"></div>
      </article>
    </section>
  </main>

  <aside class="right-panel">
    <section class="paper-ticket panel">
      <div class="panel-heading compact">
        <div><small>SIMULATION ONLY</small><h2>Paper Order</h2></div>
        <span class="paper-badge">PAPER</span>
      </div>
      <div class="bid-ask">
        <button id="sellPreset" class="sell-side"><small>SELL</small><strong id="sellPrice">--</strong></button>
        <button id="buyPreset" class="buy-side"><small>BUY</small><strong id="buyPrice">--</strong></button>
      </div>
      <label class="field-label">Quantity</label>
      <div class="stepper">
        <button id="qtyMinus">−</button>
        <input id="orderQty" type="number" min="0.0001" step="1" value="1">
        <button id="qtyPlus">+</button>
      </div>
      <div class="order-summary"><span>Estimated value</span><strong id="estimatedValue">--</strong></div>
      <div class="order-buttons">
        <button id="paperSellBtn" class="sell-order">SELL</button>
        <button id="paperBuyBtn" class="buy-order">BUY</button>
      </div>
      <p class="paper-note">ส่วนนี้เป็นเพียงการจำลองใน Browser ไม่มีการส่งคำสั่งซื้อขายจริง</p>
    </section>

    <section class="details-card panel">
      <div class="panel-heading compact"><div><small>INSTRUMENT</small><h2>Asset Details</h2></div></div>
      <dl class="asset-details">
        <div><dt>Type</dt><dd id="detailType">--</dd></div>
        <div><dt>Exchange</dt><dd id="detailExchange">--</dd></div>
        <div><dt>Currency</dt><dd id="detailCurrency">--</dd></div>
        <div><dt>Market Cap</dt><dd id="detailMarketCap">--</dd></div>
        <div><dt>Bars loaded</dt><dd id="detailBars">--</dd></div>
      </dl>
    </section>

    <section class="news-card panel">
      <div class="panel-heading compact"><div><small>HEADLINES</small><h2>Latest News</h2></div></div>
      <div id="newsList" class="news-list"><p class="empty-state">กำลังโหลดข่าว...</p></div>
    </section>
  </aside>

  <footer class="statusbar">
    <span><b>DATA:</b> Yahoo Finance via yfinance</span><span><b>CHART:</b> Lightweight Charts™ by TradingView</span>
    <span id="lastUpdated">Last update: --</span>
    <span class="warning">Educational dashboard • Not financial advice • Not an execution platform</span>
  </footer>
</div>

<div id="toast" class="toast"><strong id="toastTitle"></strong><p id="toastMessage"></p></div>
</body>
</html>
"""


SYMBOL_ALIASES = {
    "XAU/USD": "GC=F",
    "XAUUSD": "GC=F",
    "XAUUSD=X": "GC=F",
    "GOLD SPOT": "GC=F",
    "SPOT GOLD": "GC=F",
    "GOLD": "GC=F",
}

def normalize_symbol_alias(value: str | None) -> str:
    raw = (value or "").strip().upper()
    compact = raw.replace(" ", "")
    return SYMBOL_ALIASES.get(raw, SYMBOL_ALIASES.get(compact, raw))

SYMBOL_RE = re.compile(r"^[A-Za-z0-9.^=\-]{1,30}$")
VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "ytd", "1y", "2y", "5y", "10y", "max"}
VALID_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}
ALLOWED_TYPES = {
    "EQUITY", "ETF", "INDEX", "CRYPTOCURRENCY", "CURRENCY",
    "FUTURE", "MUTUALFUND", "MONEYMARKET"
}


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self) -> None:
        self._data: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def get_or_set(self, key: str, ttl: int, factory: Callable[[], Any]) -> Any:
        now = time.time()
        with self._lock:
            entry = self._data.get(key)
            if entry and entry.expires_at > now:
                return entry.value

        value = factory()

        with self._lock:
            self._data[key] = CacheEntry(value=value, expires_at=now + ttl)
            if len(self._data) > 300:
                expired = [k for k, v in self._data.items() if v.expires_at <= now]
                for old_key in expired[:150]:
                    self._data.pop(old_key, None)
        return value


cache = TTLCache()


def api_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def clean_symbol(value: str | None) -> str:
    symbol = normalize_symbol_alias(value)
    if not SYMBOL_RE.fullmatch(symbol):
        raise ValueError("รูปแบบสัญลักษณ์ไม่ถูกต้อง")
    return symbol


def clean_period(value: str | None) -> str:
    period = (value or "3mo").strip()
    if period not in VALID_PERIODS:
        raise ValueError("ช่วงเวลาไม่รองรับ")
    return period


def clean_interval(value: str | None) -> str:
    interval = (value or "1d").strip()
    if interval not in VALID_INTERVALS:
        raise ValueError("กรอบเวลาไม่รองรับ")
    return interval


def finite_or_none(value: Any) -> float | int | None:
    try:
        number = float(value)
        if math.isfinite(number):
            return number
    except (TypeError, ValueError):
        pass
    return None


def scalar(row: pd.Series, column: str) -> float | None:
    value = row.get(column)
    if isinstance(value, pd.Series):
        value = value.iloc[0] if not value.empty else None
    return finite_or_none(value)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    close = pd.to_numeric(result["Close"], errors="coerce")

    result["SMA20"] = close.rolling(20, min_periods=1).mean()
    result["SMA50"] = close.rolling(50, min_periods=1).mean()
    result["EMA20"] = close.ewm(span=20, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result["RSI14"] = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    result["MACD"] = ema12 - ema26
    result["MACD_SIGNAL"] = result["MACD"].ewm(span=9, adjust=False).mean()
    result["MACD_HIST"] = result["MACD"] - result["MACD_SIGNAL"]
    return result


def time_value(index_value: Any) -> int:
    stamp = pd.Timestamp(index_value)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    else:
        stamp = stamp.tz_convert("UTC")
    return int(stamp.timestamp())


YAHOO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}

def yahoo_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        url,
        params=params,
        headers=YAHOO_HEADERS,
        timeout=18,
    )
    if response.status_code == 429:
        raise RuntimeError("Yahoo Finance จำกัดจำนวนคำขอชั่วคราว (HTTP 429)")
    response.raise_for_status()
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("Yahoo Finance ส่งข้อมูลที่อ่านไม่ได้") from exc


def yahoo_chart_frame(
    symbol: str,
    period: str,
    interval: str,
    prepost: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urlquote(symbol, safe="")
    )
    payload = yahoo_json(
        url,
        {
            "range": period,
            "interval": interval,
            "includePrePost": str(prepost).lower(),
            "events": "div,splits",
            "includeAdjustedClose": "true",
        },
    )

    chart = payload.get("chart") or {}
    if chart.get("error"):
        description = chart["error"].get("description") or "Yahoo Finance error"
        raise LookupError(description)

    results = chart.get("result") or []
    if not results:
        raise LookupError(f"ไม่พบข้อมูลราคา {symbol}")

    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators") or {}
    quotes = indicators.get("quote") or []

    if not timestamps or not quotes:
        raise LookupError(f"ไม่พบข้อมูลแท่งราคา {symbol}")

    quote_data = quotes[0]
    length = len(timestamps)

    def values(name: str) -> list[Any]:
        raw = quote_data.get(name) or []
        return list(raw[:length]) + [None] * max(0, length - len(raw))

    df = pd.DataFrame(
        {
            "Open": values("open"),
            "High": values("high"),
            "Low": values("low"),
            "Close": values("close"),
            "Volume": values("volume"),
        },
        index=pd.to_datetime(timestamps, unit="s", utc=True),
    )

    adjclose_sets = indicators.get("adjclose") or []
    if adjclose_sets:
        raw_adj = adjclose_sets[0].get("adjclose") or []
        df["Adj Close"] = list(raw_adj[:length]) + [None] * max(0, length - len(raw_adj))

    for column in ("Open", "High", "Low", "Close", "Volume"):
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if df.empty:
        raise LookupError(f"ไม่พบข้อมูลราคาที่ใช้ได้ของ {symbol}")

    return df, (result.get("meta") or {})


def market_frame(
    symbol: str,
    period: str,
    interval: str,
    prepost: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    ใช้ Yahoo chart endpoint โดยตรงก่อน เพื่อเลี่ยงขั้นตอน consent/cookie
    ที่ yfinance บางรุ่นเรียกผ่าน guce.yahoo.com บน Cloud Hosting
    แล้วค่อย fallback ไป yfinance หาก endpoint แรกใช้งานไม่ได้
    """
    direct_error: Exception | None = None

    try:
        return yahoo_chart_frame(symbol, period, interval, prepost)
    except Exception as exc:
        direct_error = exc
        app.logger.warning("Yahoo direct endpoint failed for %s: %s", symbol, exc)

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            period=period,
            interval=interval,
            auto_adjust=False,
            actions=False,
            prepost=prepost,
            repair=False,
            timeout=15,
            raise_errors=True,
        )
        if df is None or df.empty:
            raise LookupError(f"ไม่พบข้อมูลราคา {symbol}")
        return df, {}
    except Exception as yf_error:
        raise RuntimeError(
            f"โหลดข้อมูลตลาดไม่สำเร็จ: direct={direct_error}; yfinance={yf_error}"
        ) from yf_error


def history_payload(symbol: str, period: str, interval: str, prepost: bool) -> dict[str, Any]:
    df, _meta = market_frame(symbol, period, interval, prepost)

    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(set(df.columns)):
        raise LookupError("ข้อมูลราคาที่ได้รับไม่ครบ")

    df = df.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if df.empty:
        raise LookupError(f"ไม่พบข้อมูลราคาที่ใช้ได้ของ {symbol}")

    df = add_indicators(df)

    candles = []
    volumes = []
    sma20 = []
    sma50 = []
    ema20 = []
    rsi = []
    macd = []
    macd_signal = []
    macd_hist = []

    previous_close = None

    for index, row in df.iterrows():
        timestamp = time_value(index)
        open_value = scalar(row, "Open")
        high_value = scalar(row, "High")
        low_value = scalar(row, "Low")
        close_value = scalar(row, "Close")
        volume_value = scalar(row, "Volume") or 0

        if None in (open_value, high_value, low_value, close_value):
            continue

        candles.append({
            "time": timestamp,
            "open": open_value,
            "high": high_value,
            "low": low_value,
            "close": close_value,
        })

        volumes.append({
            "time": timestamp,
            "value": max(0, int(volume_value)),
            "direction": "up" if previous_close is None or close_value >= previous_close else "down",
        })
        previous_close = close_value

        for collection, column in (
            (sma20, "SMA20"),
            (sma50, "SMA50"),
            (ema20, "EMA20"),
            (rsi, "RSI14"),
            (macd, "MACD"),
            (macd_signal, "MACD_SIGNAL"),
        ):
            indicator_value = scalar(row, column)
            if indicator_value is not None:
                collection.append({"time": timestamp, "value": indicator_value})

        hist_value = scalar(row, "MACD_HIST")
        if hist_value is not None:
            macd_hist.append({
                "time": timestamp,
                "value": hist_value,
                "direction": "up" if hist_value >= 0 else "down",
            })

    if not candles:
        raise LookupError(f"ไม่พบแท่งราคาของ {symbol}")

    first_close = candles[0]["close"]
    last_close = candles[-1]["close"]
    change = last_close - first_close
    change_percent = (change / first_close * 100) if first_close else 0

    return {
        "ok": True,
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "candles": candles,
        "volume": volumes,
        "indicators": {
            "sma20": sma20,
            "sma50": sma50,
            "ema20": ema20,
            "rsi14": rsi,
            "macd": macd,
            "macdSignal": macd_signal,
            "macdHist": macd_hist,
        },
        "summary": {
            "open": candles[-1]["open"],
            "high": candles[-1]["high"],
            "low": candles[-1]["low"],
            "close": last_close,
            "volume": volumes[-1]["value"] if volumes else 0,
            "periodChange": change,
            "periodChangePercent": change_percent,
            "bars": len(candles),
        },
    }


def quote_payload(symbol: str) -> dict[str, Any]:
    df, meta = market_frame(symbol, "5d", "1d", False)

    df = df.dropna(subset=["Close"])
    if df.empty:
        raise LookupError(f"ไม่พบราคาล่าสุดของ {symbol}")

    last = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else last

    price = finite_or_none(meta.get("regularMarketPrice")) or scalar(last, "Close") or 0
    previous_close = (
        finite_or_none(meta.get("chartPreviousClose"))
        or finite_or_none(meta.get("previousClose"))
        or scalar(previous, "Close")
        or price
    )

    change = price - previous_close
    change_percent = (change / previous_close * 100) if previous_close else 0

    return {
        "ok": True,
        "symbol": symbol,
        "name": (
            meta.get("longName")
            or meta.get("shortName")
            or meta.get("symbol")
            or symbol
        ),
        "price": price,
        "previousClose": previous_close,
        "change": change,
        "changePercent": change_percent,
        "open": finite_or_none(meta.get("regularMarketOpen")) or scalar(last, "Open"),
        "high": finite_or_none(meta.get("regularMarketDayHigh")) or scalar(last, "High"),
        "low": finite_or_none(meta.get("regularMarketDayLow")) or scalar(last, "Low"),
        "volume": finite_or_none(meta.get("regularMarketVolume")) or scalar(last, "Volume"),
        "currency": meta.get("currency") or "",
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName") or "",
        "quoteType": meta.get("instrumentType") or "",
        "marketCap": finite_or_none(meta.get("marketCap")),
        "timestamp": int(time.time()),
    }


def search_payload(query: str) -> dict[str, Any]:
    normalized = query.strip().upper()
    results: list[dict[str, Any]] = []

    gold_queries = {
        "XAU/USD", "XAUUSD", "XAUUSD=X", "XAU", "GOLD",
        "GOLD SPOT", "SPOT GOLD", "ทอง", "ทองคำ"
    }
    if normalized in gold_queries or "XAU" in normalized:
        results.append({
            "symbol": "GC=F",
            "name": "Gold Futures — Yahoo proxy for XAU/USD",
            "exchange": "COMEX",
            "type": "FUTURE",
        })

    try:
        payload = yahoo_json(
            "https://query1.finance.yahoo.com/v1/finance/search",
            {
                "q": query,
                "quotesCount": 12,
                "newsCount": 0,
                "enableFuzzyQuery": "true",
            },
        )
        raw_quotes = payload.get("quotes") or []
    except Exception as direct_error:
        app.logger.warning("Yahoo direct search failed: %s", direct_error)
        search = yf.Search(query, max_results=12, news_count=0, enable_fuzzy_query=True)
        raw_quotes = getattr(search, "quotes", []) or []

    for item in raw_quotes:
        quote_type = (item.get("quoteType") or item.get("typeDisp") or "").upper()
        symbol = (item.get("symbol") or "").upper()
        if not symbol or (quote_type and quote_type not in ALLOWED_TYPES):
            continue
        if any(existing.get("symbol") == symbol for existing in results):
            continue
        results.append({
            "symbol": symbol,
            "name": (
                item.get("shortname")
                or item.get("longname")
                or item.get("shortName")
                or item.get("longName")
                or item.get("name")
                or symbol
            ),
            "exchange": item.get("exchDisp") or item.get("exchange") or "",
            "type": quote_type or "MARKET",
        })

    return {"ok": True, "query": query, "results": results[:10]}


def news_payload(symbol: str) -> dict[str, Any]:
    try:
        payload = yahoo_json(
            "https://query1.finance.yahoo.com/v1/finance/search",
            {
                "q": symbol,
                "quotesCount": 0,
                "newsCount": 8,
                "enableFuzzyQuery": "true",
            },
        )
        raw_news = payload.get("news") or []
    except Exception as direct_error:
        app.logger.warning("Yahoo direct news failed: %s", direct_error)
        ticker = yf.Ticker(symbol)
        raw_news = ticker.get_news(count=8, tab="news") or []

    results: list[dict[str, Any]] = []

    for entry in raw_news:
        if not isinstance(entry, dict):
            continue

        content = entry.get("content")
        item = content if isinstance(content, dict) else entry

        provider = item.get("provider") or {}
        click_url = item.get("clickThroughUrl") or item.get("canonicalUrl") or {}
        thumbnail = item.get("thumbnail") or {}
        resolutions = thumbnail.get("resolutions") if isinstance(thumbnail, dict) else []

        url = (
            item.get("link")
            or (click_url.get("url") if isinstance(click_url, dict) else "")
            or ""
        )

        published = item.get("pubDate") or item.get("displayTime") or ""
        unix_time = item.get("providerPublishTime")
        if unix_time and not published:
            try:
                published = datetime.fromtimestamp(
                    int(unix_time), tz=timezone.utc
                ).isoformat()
            except Exception:
                published = ""

        publisher = (
            item.get("publisher")
            or (provider.get("displayName") if isinstance(provider, dict) else "")
            or ""
        )

        results.append({
            "title": item.get("title") or "Market news",
            "publisher": publisher,
            "url": url,
            "published": published,
            "thumbnail": (
                resolutions[0].get("url")
                if resolutions and isinstance(resolutions[0], dict)
                else ""
            ),
        })

    return {"ok": True, "symbol": symbol, "results": results[:6]}


@app.get("/")
def index():
    return render_template_string(PAGE_HTML)


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "Leng Market Terminal", "time": int(time.time())})


@app.get("/api/diagnostic")
def diagnostic():
    try:
        df, meta = market_frame("AAPL", "5d", "1d", False)
        return jsonify({
            "ok": True,
            "message": "Market data connection works",
            "rows": len(df),
            "source": "Yahoo chart endpoint / yfinance fallback",
            "currency": meta.get("currency", ""),
        })
    except Exception as exc:
        app.logger.exception("Market diagnostic failed")
        return jsonify({
            "ok": False,
            "error": str(exc),
            "yfinanceVersion": getattr(yf, "__version__", "unknown"),
        }), 502


@app.get("/api/search")
def search():
    query = (request.args.get("q") or "").strip()
    if len(query) < 1:
        return jsonify({"ok": True, "query": query, "results": []})
    try:
        payload = cache.get_or_set(f"search:{query.lower()}", 180, lambda: search_payload(query))
        return jsonify(payload)
    except Exception as exc:
        return api_error(f"ค้นหาสินทรัพย์ไม่สำเร็จ: {exc}", 502)


@app.get("/api/history")
def history():
    try:
        symbol = clean_symbol(request.args.get("symbol"))
        period = clean_period(request.args.get("period"))
        interval = clean_interval(request.args.get("interval"))
        prepost = (request.args.get("prepost") or "false").lower() == "true"
        payload = cache.get_or_set(
            f"history:{symbol}:{period}:{interval}:{prepost}",
            45 if interval in {"1m", "2m", "5m", "15m"} else 180,
            lambda: history_payload(symbol, period, interval, prepost),
        )
        return jsonify(payload)
    except ValueError as exc:
        return api_error(str(exc), 400)
    except LookupError as exc:
        return api_error(str(exc), 404)
    except Exception as exc:
        return api_error(f"โหลดกราฟไม่สำเร็จ: {exc}", 502)


@app.get("/api/quote")
def quote():
    try:
        symbol = clean_symbol(request.args.get("symbol"))
        payload = cache.get_or_set(f"quote:{symbol}", 45, lambda: quote_payload(symbol))
        return jsonify(payload)
    except ValueError as exc:
        return api_error(str(exc), 400)
    except LookupError as exc:
        return api_error(str(exc), 404)
    except Exception as exc:
        return api_error(f"โหลดราคาล่าสุดไม่สำเร็จ: {exc}", 502)


@app.get("/api/news")
def news():
    try:
        symbol = clean_symbol(request.args.get("symbol"))
        payload = cache.get_or_set(f"news:{symbol}", 600, lambda: news_payload(symbol))
        return jsonify(payload)
    except ValueError as exc:
        return api_error(str(exc), 400)
    except Exception:
        return jsonify({"ok": True, "symbol": request.args.get("symbol", ""), "results": []})


if __name__ == "__main__":
    # Railway จะกำหนด PORT ให้อัตโนมัติ
    # ถ้ารันในเครื่องจะใช้พอร์ต 5050
    port = int(os.environ.get("PORT", "5050"))
    print("=" * 62)
    print("LENG MARKET TERMINAL")
    print(f"Server running on port {port}")
    print("=" * 62)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
