package main

import (
	"encoding/json"
	"encoding/xml"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"spotprice/entsoe"
	"strconv"
	"time"
)

const (
	timeLayout = "2006010215"

	entsoeURL = "https://web-api.tp.entsoe.eu/api?securityToken=%s&documentType=A44&periodStart=%s&periodEnd=%s&in_Domain=10YFI-1--------U&out_Domain=10YFI-1--------U"
)

type printJSONFormat struct {
	// StartTime is the start time of the timeseries returned by entsoe
	StartTime time.Time
	// EndTime is the end time of the timeseries returned by entsoe
	EndTime time.Time
	// Prices contain the list of prices returned by entsoe
	Prices []Price
}

type Price struct {
	DateTime   time.Time
	PriceNoTax float64
	// Position as returned by entsoe
	Position string
}

func main() {
	inputDate := time.Now().UTC().Format(timeLayout)
	if len(os.Args) > 1 {
		// Input format year - month - day - hour : yyyymmddhh / 2023010812
		inputDate = os.Args[1]
	}

	date, err := time.Parse(timeLayout, inputDate)
	if err != nil {
		fmt.Printf("Invalid time: '%s', %v\n", inputDate, err)
		os.Exit(1)
	}

	startDate := date.Format(timeLayout) + "00"
	endDate := date.Add(time.Hour*24).Format(timeLayout) + "00"

	prices, err := fetchPrices(startDate, endDate)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("%s\n", prices)

}

func fetchPrices(startDate, endDate string) (string, error) {
	APIToken := os.Getenv("ENTSOE_TOKEN")
	if len(APIToken) == 0 {
		return "", errors.New("environment variable ENTSOE_TOKEN is not set")
	}

	r, err := http.Get(fmt.Sprintf(entsoeURL, APIToken, startDate, endDate))
	if err != nil {
		return "", fmt.Errorf("failed to GET spot price: %w", err)
	}
	defer r.Body.Close()

	xmlBody, err := io.ReadAll(r.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response: %w", err)
	}
	if r.StatusCode != 200 {
		return "", fmt.Errorf("received invalid statuscode: %d; body='%v'", r.StatusCode, string(xmlBody))
	}
	var spotPrice entsoe.PublicationMarketDocument
	if err := xml.Unmarshal(xmlBody, &spotPrice); err != nil {
		return "", fmt.Errorf("failed to unmarshal XML: %w; XML='%s'", err, xmlBody)
	}

	startTime, err := time.Parse(entsoe.TimeFormat, spotPrice.TimeSeries.Period.TimeInterval.Start)
	if err != nil {
		return "", fmt.Errorf("failed to parse time: %w", err)
	}

	endTime, err := time.Parse(entsoe.TimeFormat, spotPrice.TimeSeries.Period.TimeInterval.End)
	if err != nil {
		return "", fmt.Errorf("failed to parse time: %w", err)
	}

	prices := printJSONFormat{
		StartTime: startTime,
		EndTime:   endTime,
		Prices:    make([]Price, len(spotPrice.TimeSeries.Period.Point)),
	}

	for i, pricePoint := range spotPrice.TimeSeries.Period.Point {
		price, err := strconv.ParseFloat(pricePoint.PriceAmount, 64)
		if err != nil {
			return "", fmt.Errorf("failed to convert value from string to float: %v", err)
		}
		prices.Prices[i].PriceNoTax = price
		prices.Prices[i].DateTime = startTime.Add(time.Hour * time.Duration(i))
		prices.Prices[i].Position = pricePoint.Position
	}

	pricesJSON, err := json.Marshal(prices)
	if err != nil {
		return "", fmt.Errorf("failed to convert to json: %v", err)
	}

	return string(pricesJSON), nil
}
