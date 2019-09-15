package main

import (
	"bufio"
	"context"
	"fmt"
	"log"
	"os"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/awserr"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
)

const (
	storageTier = "Bulk"
)

func main() {
	// Bucket name
	bucket := ""

	// Load a file with a list of key names
	fileName := fmt.Sprintf("", bucket)
	file, err := os.Open(fileName)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	// Set context
	ctx := context.TODO()

	// Get the region the bucket resides
	region, err := getBucketRegion(ctx, bucket)

	fmt.Printf("Bucket %s is in %s region\n", bucket, region)

	// Setup S3 conneciton
	svc := s3.New(session.New(), &aws.Config{
		Region: aws.String(region),
	})

	// Read file line by line
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		key := scanner.Text()
		if isGlacierStorageClass(svc, bucket, key) {
			fmt.Printf("Restoring: %s\n", key)
			// Request object to be restored
			restoreObject(svc, bucket, key, storageTier, 10)
		} else {
			fmt.Print("Key: isn't of type 'GLACIER' storage class")
		}
		break
	}

	if err := scanner.Err(); err != nil {
		log.Fatal(err)
	}

	os.Exit(0)
}

func isGlacierStorageClass(svc *s3.S3, bucket, key string) bool {
	metadata := getObjectMetadata(svc, bucket, key)

	if (metadata.StorageClass != nil) && (*metadata.StorageClass == "GLACIER") {
		return true
	}

	return false
}

func getObjectMetadata(svc *s3.S3, bucket, key string) *s3.HeadObjectOutput {
	input := &s3.HeadObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	}

	result, err := svc.HeadObject(input)
	if err != nil {
		if aerr, ok := err.(awserr.Error); ok {
			switch aerr.Code() {
			default:
				fmt.Println(aerr.Error())
			}
		} else {
			// Print the error, cast err to awserr.Error to get the Code and
			// Message from an error.
			fmt.Println(err.Error())
		}
		return nil
	}

	return result

}

func getBucketRegion(ctx context.Context, bucket string) (string, error) {
	sess := session.Must(session.NewSession())

	region, err := s3manager.GetBucketRegion(ctx, sess, bucket, "us-west-2")
	if err != nil {
		if aerr, ok := err.(awserr.Error); ok && aerr.Code() == "NotFound" {
			fmt.Fprintf(os.Stderr, "unable to find bucket %s's region not found\n", bucket)
		}
		return "", err
	}
	return region, nil
}

func restoreObject(svc *s3.S3, bucket, key, tier string, days int64) error {
	input := &s3.RestoreObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
		RestoreRequest: &s3.RestoreRequest{
			Days: aws.Int64(days),
			GlacierJobParameters: &s3.GlacierJobParameters{
				Tier: aws.String(tier),
			},
		},
	}

	_, err := svc.RestoreObject(input)
	if err != nil {
		if aerr, ok := err.(awserr.Error); ok {
			switch aerr.Code() {
			case s3.ErrCodeObjectAlreadyInActiveTierError:
				fmt.Println(s3.ErrCodeObjectAlreadyInActiveTierError, aerr.Error())
			case "InvalidObjectState":
				fmt.Println("Can't restore object its not of storage class type 'GLACIER'")
			case "RestoreAlreadyInProgress":
				fmt.Println("Restore already in progess")
			default:
				fmt.Println(aerr.Error())
			}
		} else {
			// Print the error, cast err to awserr.Error to get the Code and
			// Message from an error.
			fmt.Println(err.Error())
		}
		return err
	}

	return nil
}
